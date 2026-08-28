from __future__ import annotations

from getpass import getpass
from pathlib import Path

from auth import AuthStore, ROLE_MANAGER


def main() -> None:
    root = Path(__file__).resolve().parent
    store = AuthStore(root / "usuarios.db")
    print("Criação de conta de gestor")
    cpf = input("CPF do gestor: ").strip()
    nome = input("Nome do gestor: ").strip() or "Gestor"
    senha = getpass("Senha (mínimo 8 caracteres): ")
    confirmacao = getpass("Confirme a senha: ")
    if senha != confirmacao:
        raise SystemExit("As senhas não coincidem.")
    try:
        user = store.create_user(cpf, senha, nome, ROLE_MANAGER)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Gestor criado com sucesso: {user.name} ({user.cpf_display})")


if __name__ == "__main__":
    main()
