from typing import List

from model.perfil import Perfil
from model.usuario import Usuario


class RecepcionistaController:
    """Controlador de gestão de recepcionistas — UC2 e UC3."""

    def cadastrarRecepcionista(self, nome: str, login: str, senha: str) -> str:
        nome_limpo = (nome or "").strip()
        login_limpo = (login or "").strip()
        senha_limpa = (senha or "").strip()

        if not nome_limpo or not login_limpo or not senha_limpa:
            return "Preencha todos os campos obrigatórios"

        if Usuario.existeLogin(login_limpo):
            return "Login já utilizado"

        novaRecepcionista = Usuario()
        novaRecepcionista.setNome(nome_limpo)
        novaRecepcionista.setLogin(login_limpo)
        novaRecepcionista.setSenha(senha)
        novaRecepcionista.setPerfil(Perfil.RECEPCIONISTA)
        novaRecepcionista.salvar()

        return "Recepcionista cadastrada com sucesso!"

    def listarRecepcionistas(self) -> List[Usuario]:
        return Usuario.listarRecepcionistas()

    def editarRecepcionista(self, id: int, nome: str, novaSenha: str = "") -> str:
        nome_limpo = (nome or "").strip()
        if not isinstance(id, int) or id <= 0 or not nome_limpo:
            return "Dados inválidos"

        recepcionista = Usuario.buscarPorId(id)
        if recepcionista is None or recepcionista.getPerfil() != Perfil.RECEPCIONISTA:
            return "Dados inválidos"

        recepcionista.setNome(nome_limpo)
        if novaSenha and novaSenha.strip():
            recepcionista.setSenha(novaSenha)

        recepcionista.salvar()
        return "Recepcionista atualizada com sucesso!"
