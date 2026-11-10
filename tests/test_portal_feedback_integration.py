from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from auth import AuthStore
from petsus import config
from petsus.dashboard.navigation import navigation_for


@pytest.fixture
def portal_source(tmp_path, monkeypatch):
    source = pd.read_excel(config.DATA_FILE, sheet_name="base_processos", nrows=20)
    source.loc[source.index[0], ["desfecho", "urgente", "liminar"]] = ["Em andamento", "Não", "Não"]
    path = tmp_path / "demo.xlsx"
    source.to_excel(path, sheet_name="base_processos", index=False)
    database = tmp_path / "portal.db"
    monkeypatch.setattr(config, "DATA_FILE", path)
    monkeypatch.setattr(config, "DATABASE_FILE", database)
    monkeypatch.delenv("PETSUS_GESTOR_CPF", raising=False)
    monkeypatch.delenv("PETSUS_GESTOR_SENHA", raising=False)
    return source, AuthStore(database)


def authenticated_app(user):
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30)
    app.session_state["auth_user"] = user.__dict__
    app.session_state["auth_mfa_verified"] = True
    return app.run()


def test_patient_portal_has_only_own_processes_and_no_analytics(portal_source):
    source, store = portal_source
    patient_id = str(source.iloc[0]["paciente_id"])
    user = store.create_user("12345678900", "senha-teste-segura", "Paciente de teste", "usuario", patient_id, email="patient@example.com")
    app = authenticated_app(user)
    assert not app.exception
    navigation = app.sidebar.radio[0]
    assert navigation.options == navigation_for(False)[0]
    assert not app.multiselect
    assert not app.date_input
    assert not app.get("plotly_chart")
    assert len(app.selectbox[0].options) == source[source["paciente_id"].astype(str).eq(patient_id)]["processo_id"].nunique()
    assert not any("Taxa de Procedência" in item.value for item in app.markdown)
    for page in navigation.options[1:]:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, page
        assert not app.get("plotly_chart"), page
    assert app.text_area


def test_feedback_is_registered_and_patient_can_track_own_report(portal_source):
    source, store = portal_source
    user = store.create_user("12345678900", "senha-teste-segura", "Paciente de teste", "usuario", str(source.iloc[0]["paciente_id"]), email="patient@example.com")
    app = authenticated_app(user)
    app.sidebar.radio[0].set_value("Ajuda e contato").run()
    app.text_area[0].input("O prazo apresentado precisa ser conferido pela equipe.")
    next(button for button in app.button if button.label == "Registrar relato").click().run()
    assert not app.exception
    assert any("Relato #" in item.value for item in app.success)
    assert any("Recebido" in item.label for item in app.expander)


def test_every_manager_page_renders_and_empty_results_are_handled(portal_source):
    _, store = portal_source
    user = store.create_user("98765432100", "senha-teste-segura", "Gestor de teste", "gestor", must_change_password=False)
    app = authenticated_app(user)
    assert not app.exception
    for page in navigation_for(True)[0][1:]:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, page
    app.sidebar.radio[0].set_value("Visão Geral").run()
    app.text_input(key="filter_search").input("nenhum-resultado-inexistente").run()
    assert not app.exception
    assert any("Nenhum registro encontrado" in item.value for item in app.warning)
    app.button(key="clear_filters_button").click().run()
    assert not app.exception
    assert app.text_input(key="filter_search").value == ""
    assert not any("Nenhum registro encontrado" in item.value for item in app.warning)
    app.button(key="patient_contrast").click().run()
    assert not app.exception
    assert app.session_state["a11y_contrast"] is True
    assert app.sidebar.radio[0].options == navigation_for(True)[0]


def test_patient_missing_from_source_can_still_logout_and_report(portal_source):
    _, store = portal_source
    user = store.create_user("12345678900", "senha-teste-segura", "Paciente", "usuario", "PAC_REMOVIDO", email="missing@example.com")
    app = authenticated_app(user)
    assert not app.exception
    assert any("Não foram encontrados dados" in item.value for item in app.error)
    assert any(button.label == "Sair" for button in app.sidebar.button)
    app.sidebar.radio[0].set_value("Ajuda e contato").run()
    assert not app.exception
    assert app.text_area
    assert app.selectbox[1].options == ["Sem processo específico"]


def test_report_shortcut_opens_help_with_the_selected_patient_process(portal_source):
    source, store = portal_source
    user = store.create_user("12345678900", "senha-teste-segura", "Paciente", "usuario", str(source.iloc[0]["paciente_id"]), email="patient@example.com")
    app = authenticated_app(user)
    selected_process = app.selectbox(key="patient_process").value
    app.button(key="patient_report_button").click().run()
    assert not app.exception
    assert app.sidebar.radio[0].value == "Ajuda e contato"
    assert app.selectbox(key="feedback_process").value == selected_process


def test_patient_header_accessibility_controls_change_preferences(portal_source):
    source, store = portal_source
    user = store.create_user("12345678900", "senha-teste-segura", "Paciente", "usuario", str(source.iloc[0]["paciente_id"]), email="patient@example.com")
    app = authenticated_app(user)
    app.button(key="patient_text_large").click().run()
    assert not app.exception
    assert app.session_state["a11y_large_text"] is True
    app.button(key="patient_contrast").click().run()
    assert not app.exception
    assert app.session_state["a11y_contrast"] is True
    app.button(key="patient_text_small").click().run()
    assert not app.exception
    assert app.session_state["a11y_large_text"] is False
    assert app.sidebar.radio[0].value == "Meu acompanhamento"
