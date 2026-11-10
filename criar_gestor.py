from __future__ import annotations

from getpass import getpass
from pathlib import Path

from petsus.auth.application import AuthStore, ROLE_MANAGER
from petsus.auth.registration import is_valid_email, normalize_email


def main() -> None:
    root = Path(__file__).resolve().parent
    store = AuthStore(root / "usuarios.db")
    print("Criação de conta de gestor")
    cpf = input("CPF do gestor: ").strip()
    nome = input("Nome do gestor: ").strip() or "Gestor"
    email = normalize_email(input("E-mail do gestor (para segundo fator): "))
    if not is_valid_email(email):
        raise SystemExit("Informe um e-mail válido.")
    senha = getpass("Senha inicial (mínimo 8 caracteres): ")
    confirmacao = getpass("Confirme a senha: ")
    if senha != confirmacao:
        raise SystemExit("As senhas não coincidem.")
    try:
        user = store.create_user(cpf, senha, nome, ROLE_MANAGER, email=email, must_change_password=True)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Gestor criado com sucesso: {user.name} ({user.cpf_display})")
    print("A senha inicial deverá ser trocada no primeiro acesso. Configure SMTP para ativar o segundo fator por e-mail.")


if __name__ == "__main__":
    main()
