from __future__ import annotations

from datetime import date

import streamlit as st

from petsus.auth.application import AuthStore
from petsus.auth.models import ROLE_MANAGER, ROLE_USER
from petsus.auth.registration import is_valid_email, normalize_email
from petsus.auth.email import mfa_required, smtp_configured
from petsus.dashboard.support import local_timestamp


def _acting_manager_id() -> int:
    state = st.session_state.get("auth_user", {})
    return int(state.get("id", 0)) if isinstance(state, dict) else 0


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
    st.caption("Crie contas administrativas individualmente. A senha inicial deverá ser trocada no primeiro acesso.")
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
            store.create_user(cpf, password, name, ROLE_MANAGER, email=normalized_email,
                              must_change_password=True, acting_manager_id=_acting_manager_id())
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
            acting_manager_id=_acting_manager_id(),
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
            acting_manager_id=_acting_manager_id(),
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
    st.caption("A consulta detalhada é feita por CPF e retorna no máximo uma conta. A revisão de acessos usa dados reduzidos.")
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
    if not account.get("active"):
        st.warning("Esta conta está com acesso revogado. Use a revisão de acessos para reativá-la.")
        return
    if account["role"] == ROLE_MANAGER:
        _manager_edit_form(store, account)
    else:
        _patient_edit_form(store, account)
    st.divider()
    _delete_account_form(store, account, acting_manager_id)


def render_internal_management(store: AuthStore) -> None:
    manager_id = _acting_manager_id()
    user = store.get_active_user(manager_id) if manager_id else None
    session = st.session_state.get("auth_user", {})
    if (user is None or not user.is_manager or user.must_change_password
            or not isinstance(session, dict) or session.get("session_version") != user.session_version
            or (store.requires_second_factor(user) and st.session_state.get("auth_mfa_verified") is not True)):
        st.error("Esta área exige uma sessão válida de gestor. Entre novamente para continuar.")
        return
    st.info("Área restrita a gestores. Revise periodicamente as contas e revogue acessos que não sejam mais necessários.")
    if smtp_configured():
        st.caption("Segundo fator por e-mail habilitado. Contas precisam de e-mail válido para entrar.")
    elif mfa_required():
        st.error("Segundo fator obrigatório sem SMTP configurado. Configure o envio antes de encerrar esta sessão.")
    else:
        st.warning("Segundo fator indisponível: configure o SMTP para habilitar códigos de acesso por e-mail. Para exigir o segundo fator mesmo sem SMTP, defina PETSUS_REQUIRE_MFA=true.")
    create_tab, edit_tab, review_tab, audit_tab = st.tabs(["Adicionar gestor", "Consultar por CPF", "Revisar acessos", "Auditoria"])
    with create_tab:
        _manager_create_form(store)
    with edit_tab:
        _account_lookup(store, manager_id)
    with review_tab:
        _access_review(store, manager_id)
    with audit_tab:
        _audit_trail(store, manager_id)


def _access_review(store: AuthStore, manager_id: int) -> None:
    st.markdown("### Revisão periódica de acessos")
    st.caption("Até 500 contas. A listagem mostra somente identificador, CPF mascarado, perfil, situação e datas. Para detalhes, consulte um CPF.")
    accounts = store.list_accounts(manager_id)
    if not accounts:
        st.info("Nenhuma conta encontrada.")
        return
    records = [{
        "Conta": row["id"], "CPF mascarado": row["cpf_display"],
        "Perfil": "Gestor" if row["role"] == ROLE_MANAGER else "Paciente",
        "Acesso": "Ativo" if row["active"] else "Revogado",
        "Troca de senha pendente": "Sim" if row["must_change_password"] else "Não",
        "Criada em": local_timestamp(row["created_at"]), "Último acesso": local_timestamp(row["last_login"]) if row["last_login"] else "Sem registro",
    } for row in accounts]
    st.dataframe(records, hide_index=True, use_container_width=True)
    selected = st.selectbox(
        "Conta a revisar", accounts, format_func=lambda row: f"Conta {row['id']} · {row['cpf_display']} · {row['role']}",
    )
    active = bool(selected["active"])
    action = "Revogar acesso" if active else "Reativar acesso"
    with st.form("review_account_access"):
        confirmed = st.checkbox(f"Confirmo a ação: {action.lower()} da conta {selected['id']}.")
        submitted = st.form_submit_button(action)
    if submitted:
        if not confirmed:
            st.error("Confirme a alteração de acesso.")
        else:
            try:
                store.set_account_active(int(selected["id"]), not active, manager_id)
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.session_state.pop("internal_management_account", None)
                st.session_state["internal_management_notice"] = "Acesso atualizado. As sessões anteriores foram invalidadas."
                st.rerun()


def _audit_trail(store: AuthStore, manager_id: int) -> None:
    st.markdown("### Trilha de auditoria")
    st.caption("Últimos 200 eventos, sem senhas, códigos, CPF completo ou dados de saúde. Horários de Fortaleza.")
    events = store.audit_events(manager_id)
    labels = {
        "login": "Entrada", "logout": "Saída", "password_check": "Verificação de senha",
        "mfa_issued": "Código de segundo fator solicitado", "mfa_check": "Verificação de segundo fator",
        "mfa_delivery_failed": "Falha no envio de segundo fator", "password_changed": "Senha alterada",
        "account_created": "Conta criada", "account_updated": "Conta atualizada", "account_deleted": "Conta excluída",
        "account_access_review": "Revisão de acessos consultada", "access_activated": "Acesso ativado", "access_revoked": "Acesso revogado",
    }
    outcomes = {"success": "Concluído", "failed": "Falhou", "rate_limited": "Limite de tentativas"}
    records = [{
        "Data": local_timestamp(event["created_at"]), "Evento": labels.get(str(event["event"]), event["event"]),
        "Responsável (conta)": event["actor_id"], "Conta afetada": event["subject_id"],
        "Resultado": outcomes.get(str(event["outcome"]), event["outcome"]),
    } for event in events]
    st.dataframe(records, hide_index=True, use_container_width=True)
