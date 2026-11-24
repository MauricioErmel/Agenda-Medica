from typing import Optional

from model.usuario import Usuario


class AuthController:
    """Controlador de autenticação — UC1: Entrar no Sistema."""

    def entrar(self, login: str, senha: str) -> Optional[Usuario]:
        login_limpo = (login or "").strip()
        if not login_limpo or not senha:
            return None
        return Usuario.autenticar(login_limpo, senha)
