from dataclasses import dataclass

ROLE_USER = "usuario"
ROLE_MANAGER = "gestor"


@dataclass(frozen=True)
class AuthUser:
    id: int
    name: str
    role: str
    patient_id: str | None
    cpf_display: str
    must_change_password: bool = False
    session_version: int = 1

    @property
    def is_manager(self) -> bool:
        return self.role == ROLE_MANAGER

