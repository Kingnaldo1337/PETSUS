from __future__ import annotations

from datetime import date

import streamlit as st

from auth import AuthStore
from petsus.auth.models import ROLE_MANAGER, ROLE_USER
from petsus.auth.registration import is_valid_email, normalize_email


def _account_summary(account: dict[str, object]) -> None:
    role_label = "Gestor" if account["role"] == ROLE_MANAGER else "Paciente"
    with st.container(border=True):
        st.markdown(f"#### {account['name']}")
        st.caption(f"{role_label} · CPF {account['cpf_display']}")
        st.write(f"**E-mail:** {account.get('email') or 'Não cadastrado'}")
        if account["role"] == ROLE_USER:
            st.write(f"**Paciente vinculado:** {account.get('patient_id') or 'Não informado'}")
            status = "Cadastrada" if account.get("has_birth_date") else "Não cadastrada"
            st.write(f"**Data de nascimento:** {status}")


def _manager_create_form(store: AuthStore) -> None:
    st.markdown("### Adicionar gestor")
    st.caption("Crie contas administrativas individualmente. Todos os campos são obrigatórios.")
    with st.form("internal_create_manager", clear_on_submit=True):
        name = st.text_input("Nome completo")
        cpf = st.text_input("CPF", placeholder="000.000.000-00")
        email = st.text_input("E-mail", autocomplete="email")
        password = st.text_input("Senha inicial", type="password", autocomplete="new-password")
        confirmation = st.text_input("Confirmar senha", type="password", autocomplete="new-password")
        submitted = st.form_submit_button("Adicionar gestor", type="primary")
    if not submitted:
        return
    normalized_email = normalize_email(email)
    if not name.strip():
        st.error("Informe o nome do gestor.")
    elif not is_valid_email(normalized_email):
        st.error("Informe um e-mail válido.")
    elif password != confirmation:
        st.error("A confirmação não corresponde à senha.")
    else:
        try:
            store.create_user(cpf, password, name, ROLE_MANAGER, email=normalized_email)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.success("Gestor adicionado com sucesso.")


def _manager_edit_form(store: AuthStore, account: dict[str, object]) -> None:
    with st.form(f"edit_manager_{account['id']}"):
        email = st.text_input("E-mail do gestor", value=str(account.get("email") or ""))
        new_password = st.text_input(
            "Nova senha", type="password", help="Deixe em branco para manter a senha atual."
        )
        confirmation = st.text_input("Confirmar nova senha", type="password")
        submitted = st.form_submit_button("Salvar alterações", type="primary")
    if not submitted:
        return
    if new_password != confirmation:
        st.error("A confirmação não corresponde à nova senha.")
        return
    try:
        store.update_account_by_manager(
            int(account["id"]), ROLE_MANAGER,
            email=email,
            new_password=new_password or None,
        )
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.success("Dados do gestor atualizados com sucesso.")
        account["email"] = normalize_email(email)


def _patient_edit_form(store: AuthStore, account: dict[str, object]) -> None:
    with st.form(f"edit_patient_{account['id']}"):
        email = st.text_input("E-mail do paciente", value=str(account.get("email") or ""))
        change_birth_date = st.checkbox("Alterar data de nascimento")
        birth_date = st.date_input(
            "Nova data de nascimento",
            value=None,
            max_value=date.today(),
            format="DD/MM/YYYY",
            disabled=not change_birth_date,
        )
        new_password = st.text_input(
            "Nova senha", type="password", help="Deixe em branco para manter a senha atual."
        )
        confirmation = st.text_input("Confirmar nova senha", type="password")
        submitted = st.form_submit_button("Salvar alterações", type="primary")
    if not submitted:
        return
    if new_password != confirmation:
        st.error("A confirmação não corresponde à nova senha.")
        return
    if change_birth_date and birth_date is None:
        st.error("Informe a nova data de nascimento.")
        return
    try:
        store.update_account_by_manager(
            int(account["id"]), ROLE_USER,
            email=email,
            new_password=new_password or None,
            birth_date=birth_date.isoformat() if change_birth_date and birth_date else None,
        )
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.success("Dados do paciente atualizados com sucesso.")
        account["email"] = normalize_email(email)
        if change_birth_date:
            account["has_birth_date"] = True


def _delete_account_form(
    store: AuthStore, account: dict[str, object], acting_manager_id: int
) -> None:
    st.markdown("### Excluir conta")
    if int(account["id"]) == acting_manager_id:
        st.info("Sua própria conta não pode ser excluída enquanto você está conectado.")
        return
    st.warning(
        "Esta ação exclui a conta e remove imediatamente o acesso ao sistema. "
        "Os processos e dados de saúde do paciente não serão apagados."
    )
    with st.form(f"delete_account_{account['id']}"):
        confirmed = st.checkbox(
            f"Confirmo a exclusão da conta de {account['name']}."
        )
        submitted = st.form_submit_button("Excluir conta")
    if not submitted:
        return
    if not confirmed:
        st.error("Marque a confirmação antes de excluir a conta.")
        return
    try:
        store.delete_account_by_manager(
            int(account["id"]), str(account["role"]), acting_manager_id
        )
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.session_state.pop("internal_management_account", None)
        st.session_state["internal_management_notice"] = "Conta excluída com sucesso."
        st.rerun()


def _account_lookup(store: AuthStore, acting_manager_id: int) -> None:
    notice = st.session_state.pop("internal_management_notice", None)
    if notice:
        st.success(str(notice))
    st.markdown("### Consultar, editar ou excluir conta")
    st.caption("A consulta é feita somente por CPF e retorna no máximo uma conta.")
    with st.form("internal_account_lookup"):
        cpf = st.text_input("CPF da conta", placeholder="000.000.000-00")
        searched = st.form_submit_button("Consultar", type="primary")
    if searched:
        try:
            account = store.find_account_by_cpf(cpf)
        except ValueError as exc:
            st.error(str(exc))
            st.session_state.pop("internal_management_account", None)
        else:
            st.session_state["internal_management_account"] = account
            if account is None:
                st.warning("Nenhuma conta foi encontrada para o CPF informado.")

    account = st.session_state.get("internal_management_account")
    if not account:
        return
    _account_summary(account)
    if account["role"] == ROLE_MANAGER:
        _manager_edit_form(store, account)
    else:
        _patient_edit_form(store, account)
    st.divider()
    _delete_account_form(store, account, acting_manager_id)


def render_internal_management(store: AuthStore) -> None:
    st.info(
        "Área restrita a gestores. Para reduzir carga e proteger os dados, não há listagem de usuários: "
        "cada conta deve ser consultada pelo CPF completo."
    )
    create_tab, edit_tab = st.tabs(["Adicionar gestor", "Consultar por CPF"])
    with create_tab:
        _manager_create_form(store)
    with edit_tab:
        auth_state = st.session_state.get("auth_user", {})
        acting_manager_id = int(auth_state.get("id", 0)) if isinstance(auth_state, dict) else 0
        _account_lookup(store, acting_manager_id)
