"""Provisionamento explícito de duas contas de teste por configuração privada."""
from __future__ import annotations

from petsus.auth.email import setting
from petsus.auth.models import ROLE_MANAGER, ROLE_USER


def test_mode_enabled() -> bool:
    return setting("PETSUS_TEST_MODE").lower() in {"true", "1", "yes", "sim"}


def bootstrap_test_accounts(store, base) -> None:
    if not test_mode_enabled():
        return
    entries = []
    for prefix, role in [("GESTOR", ROLE_MANAGER), ("PACIENTE", ROLE_USER)]:
        cpf = store.normalize_cpf(setting(f"PETSUS_TEST_{prefix}_CPF"))
        password = setting(f"PETSUS_TEST_{prefix}_SENHA")
        if len(cpf) != 11 or len(password) < 8:
            raise ValueError("Configure CPF com 11 dígitos e senha de pelo menos 8 caracteres para as duas contas de teste nos Secrets.")
        with store._connect() as conn:
            existing = conn.execute("SELECT * FROM users WHERE cpf_lookup = ?", (store._lookup_key(cpf),)).fetchone()
        if existing is not None and (not existing["is_test_account"] or existing["role"] != role):
            raise ValueError("Um CPF de teste já pertence a uma conta normal ou a outro perfil. Escolha CPFs de teste diferentes; contas existentes não serão modificadas.")
        entries.append((prefix, role, cpf, password, existing))
    if entries[0][2] == entries[1][2]:
        raise ValueError("O gestor e o paciente de teste precisam de CPFs diferentes.")
    if entries[1][4] is None:
        if base.empty or "paciente_id" not in base:
            raise ValueError("A base precisa conter um paciente para vincular a conta de teste.")
        configured_patient = setting("PETSUS_TEST_PACIENTE_ID")
        with store._connect() as conn:
            used = {str(row[0]) for row in conn.execute("SELECT patient_id FROM users WHERE patient_id IS NOT NULL")}
        available = [str(value) for value in base["paciente_id"].dropna().unique() if str(value) not in used]
        patient_id = configured_patient or next(iter(available), "")
        if patient_id not in available:
            raise ValueError("Não há paciente livre para a conta de teste. Escolha em PETSUS_TEST_PACIENTE_ID um paciente da base que ainda não tenha conta.")
    else:
        patient_id = entries[1][4]["patient_id"]
    for prefix, role, cpf, password, existing in entries:
        if existing is not None:
            continue  # Não troca senhas, não reativa contas nem altera vínculos existentes.
        store.create_user(cpf, password, f"{prefix.title()} de teste", role,
            patient_id=patient_id if role == ROLE_USER else None,
            email=f"dashjus.teste.{prefix.lower()}@example.invalid",
            must_change_password=False, is_test_account=True)
