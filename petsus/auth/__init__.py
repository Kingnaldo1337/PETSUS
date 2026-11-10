"""Serviços de autenticação independentes da interface."""

from .application import AuthStore, logout, render_auth_gate
from .models import AuthUser, ROLE_MANAGER, ROLE_USER

__all__ = [
    "AuthStore",
    "AuthUser",
    "ROLE_MANAGER",
    "ROLE_USER",
    "logout",
    "render_auth_gate",
]

