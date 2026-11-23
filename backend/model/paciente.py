from __future__ import annotations

import re
from datetime import date, datetime
from typing import List, Optional

from database import Database
from model.sexo import Sexo
from model.situacao import Situacao


class Paciente:
    """Entidade Paciente conforme Diagrama de Classes (v2) — Ciclo 2."""

    def __init__(self) -> None:
        self.__id: Optional[int] = None
        self.__cpf: str = ""
        self.__nome: str = ""
        self.__dataNascimento: Optional[date] = None
        self.__sexo: Optional[Sexo] = None
        self.__telefone: str = ""
        self.__situacao: Optional[Situacao] = None

    def getId(self) -> Optional[int]:
        return self.__id

    def setId(self, id: int) -> None:
        self.__id = id

    def getCpf(self) -> str:
        return self.__cpf

    def setCpf(self, cpf: str) -> None:
        self.__cpf = Paciente._normalizar_cpf(cpf)

    def getNome(self) -> str:
        return self.__nome

    def setNome(self, nome: str) -> None:
        self.__nome = nome

    def getDataNascimento(self) -> Optional[date]:
        return self.__dataNascimento

    def setDataNascimento(self, dataNascimento: date) -> None:
        self.__dataNascimento = dataNascimento

    def getSexo(self) -> Optional[Sexo]:
        return self.__sexo

    def setSexo(self, sexo: Sexo) -> None:
        self.__sexo = sexo

    def getTelefone(self) -> str:
        return self.__telefone

    def setTelefone(self, telefone: str) -> None:
        self.__telefone = telefone

    def getSituacao(self) -> Optional[Situacao]:
        return self.__situacao

    def setSituacao(self, situacao: Situacao) -> None:
        self.__situacao = situacao

    @staticmethod
    def _normalizar_cpf(cpf: str) -> str:
        return re.sub(r"\D", "", cpf or "")

    @staticmethod
    def _converter_data(valor: object) -> Optional[date]:
        if isinstance(valor, datetime):
            return valor.date()
        if isinstance(valor, date):
            return valor
        if isinstance(valor, str):
            texto = valor.strip()
            if not texto:
                return None
            try:
                return date.fromisoformat(texto)
            except ValueError:
                return None
        return None

    @staticmethod
    def _montar_paciente(linha: dict) -> Paciente:
        paciente = Paciente()
        paciente.setId(int(linha["id"]))
        paciente.setCpf(linha["cpf"])
        paciente.setNome(linha["nome"])
        data_nasc = Paciente._converter_data(linha["data_nascimento"])
        if data_nasc is not None:
            paciente.setDataNascimento(data_nasc)
        paciente.setSexo(Sexo(linha["sexo"]))
        paciente.setTelefone(linha["telefone"])
        paciente.setSituacao(Situacao(linha["situacao"]))
        return paciente

    @staticmethod
    def buscarPorCpf(cpf: str) -> Optional[Paciente]:
        cpf_limpo = Paciente._normalizar_cpf(cpf)
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, cpf, nome, data_nascimento, sexo, telefone, situacao
                FROM pacientes
                WHERE cpf = %s
                LIMIT 1
                """,
                (cpf_limpo,),
            )
            linha = cursor.fetchone()
            cursor.close()
            if not linha:
                return None
            return Paciente._montar_paciente(linha)
        finally:
            conexao.close()

    @staticmethod
    def buscarPorFiltro(termo: str) -> List[Paciente]:
        termo_limpo = (termo or "").strip()
        if not termo_limpo:
            return []

        somente_digitos = re.sub(r"\D", "", termo_limpo)
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor(dictionary=True)
            if somente_digitos and not re.search(r"[A-Za-zÀ-ÿ]", termo_limpo):
                cursor.execute(
                    """
                    SELECT id, cpf, nome, data_nascimento, sexo, telefone, situacao
                    FROM pacientes
                    WHERE cpf LIKE %s OR nome LIKE %s
                    ORDER BY nome ASC
                    """,
                    (f"%{somente_digitos}%", f"%{termo_limpo}%"),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, cpf, nome, data_nascimento, sexo, telefone, situacao
                    FROM pacientes
                    WHERE nome LIKE %s
                    ORDER BY nome ASC
                    """,
                    (f"%{termo_limpo}%",),
                )
            linhas = cursor.fetchall()
            cursor.close()
            return [Paciente._montar_paciente(linha) for linha in linhas]
        finally:
            conexao.close()

    @staticmethod
    def buscarPorId(id: int) -> Optional[Paciente]:
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, cpf, nome, data_nascimento, sexo, telefone, situacao
                FROM pacientes
                WHERE id = %s
                LIMIT 1
                """,
                (id,),
            )
            linha = cursor.fetchone()
            cursor.close()
            if not linha:
                return None
            return Paciente._montar_paciente(linha)
        finally:
            conexao.close()

    def salvar(self) -> bool:
        if (
            self.__dataNascimento is None
            or self.__sexo is None
            or self.__situacao is None
        ):
            raise ValueError("Data de nascimento, sexo e situação são obrigatórios.")

        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor()
            if self.__id is None:
                cursor.execute(
                    """
                    INSERT INTO pacientes (cpf, nome, data_nascimento, sexo, telefone, situacao)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.__cpf,
                        self.__nome,
                        self.__dataNascimento,
                        self.__sexo.value,
                        self.__telefone,
                        self.__situacao.value,
                    ),
                )
                self.__id = int(cursor.lastrowid)
            else:
                # RN01: o CPF nunca é alterado na edição
                cursor.execute(
                    """
                    UPDATE pacientes
                    SET nome = %s, data_nascimento = %s, sexo = %s, telefone = %s, situacao = %s
                    WHERE id = %s
                    """,
                    (
                        self.__nome,
                        self.__dataNascimento,
                        self.__sexo.value,
                        self.__telefone,
                        self.__situacao.value,
                        self.__id,
                    ),
                )
            conexao.commit()
            cursor.close()
            return True
        except Exception:
            conexao.rollback()
            raise
        finally:
            conexao.close()

    def to_dict(self) -> dict:
        return {
            "id": self.__id,
            "cpf": self.__cpf,
            "nome": self.__nome,
            "dataNascimento": self.__dataNascimento.isoformat() if self.__dataNascimento else None,
            "sexo": self.__sexo.value if self.__sexo else None,
            "telefone": self.__telefone,
            "situacao": self.__situacao.value if self.__situacao else None,
        }
