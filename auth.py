"""Compatibilidade para importações antigas do módulo de autenticação.

O alias mantém uma única implementação e os mesmos pontos de configuração
independentemente do caminho usado pelo consumidor.
"""
from __future__ import annotations

import sys

from petsus.auth import application as _application

sys.modules[__name__] = _application
