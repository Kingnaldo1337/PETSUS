"""Serviços de autenticação independentes da interface."""

from .models import AuthUser, ROLE_MANAGER, ROLE_USER

__all__ = ["AuthUser", "ROLE_MANAGER", "ROLE_USER"]

