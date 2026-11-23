from __future__ import annotations

from typing import List, Optional

from database import Database


class Especialidade:
    """Entidade Especialidade conforme Diagrama de Classes (v2) — Ciclo 2."""

    def __init__(self) -> None:
        self.__id: Optional[int] = None
        self.__nome: str = ""

    def getId(self) -> Optional[int]:
        return self.__id

    def setId(self, id: int) -> None:
        self.__id = id

    def getNome(self) -> str:
        return self.__nome

    def setNome(self, nome: str) -> None:
        self.__nome = nome

    @staticmethod
    def _montar_especialidade(linha: dict) -> Especialidade:
        especialidade = Especialidade()
        especialidade.setId(int(linha["id"]))
        especialidade.setNome(linha["nome"])
        return especialidade

    @staticmethod
    def listarTodas() -> List[Especialidade]:
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute("SELECT id, nome FROM especialidades ORDER BY nome ASC")
            linhas = cursor.fetchall()
            cursor.close()
            return [Especialidade._montar_especialidade(linha) for linha in linhas]
        finally:
            conexao.close()

    @staticmethod
    def buscarPorId(id: int) -> Optional[Especialidade]:
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, nome FROM especialidades WHERE id = %s LIMIT 1",
                (id,),
            )
            linha = cursor.fetchone()
            cursor.close()
            if not linha:
                return None
            return Especialidade._montar_especialidade(linha)
        finally:
            conexao.close()

    def to_dict(self) -> dict:
        return {
            "id": self.__id,
            "nome": self.__nome,
        }
