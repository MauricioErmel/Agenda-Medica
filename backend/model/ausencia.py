from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

import config
from database import Database
from model.especialidade import Especialidade
from model.medico import Medico
from model.situacao import Situacao


class Ausencia:
    """Entidade Ausencia conforme Diagrama de Classes (v4) — Ciclo 4."""

    def __init__(self) -> None:
        self.__id: Optional[int] = None
        self.__medico: Optional[Medico] = None
        self.__motivo: str = ""
        self.__dataInicial: Optional[date] = None
        self.__dataFinal: Optional[date] = None

    def getId(self) -> Optional[int]:
        return self.__id

    def setId(self, id: int) -> None:
        self.__id = id

    def getMedico(self) -> Optional[Medico]:
        return self.__medico

    def setMedico(self, medico: Medico) -> None:
        if medico is None:
            raise ValueError("Médico é obrigatório para a ausência (multiplicidade 1).")
        self.__medico = medico

    def getMotivo(self) -> str:
        return self.__motivo

    def setMotivo(self, motivo: str) -> None:
        self.__motivo = motivo

    def getDataInicial(self) -> Optional[date]:
        return self.__dataInicial

    def setDataInicial(self, dataInicial: date) -> None:
        self.__dataInicial = dataInicial

    def getDataFinal(self) -> Optional[date]:
        return self.__dataFinal

    def setDataFinal(self, dataFinal: date) -> None:
        self.__dataFinal = dataFinal

    @staticmethod
    def _agora_clinica() -> datetime:
        return config.agora_clinica()

    @staticmethod
    def _converter_data(valor: object) -> Optional[date]:
        if isinstance(valor, datetime):
            return valor.date()
        if isinstance(valor, date):
            return valor
        if isinstance(valor, str) and valor.strip():
            try:
                return date.fromisoformat(valor.strip())
            except ValueError:
                return None
        return None

    @staticmethod
    def _montar_ausencia(linha: dict) -> Ausencia:
        especialidade = Especialidade()
        especialidade.setId(int(linha["especialidade_id"]))
        especialidade.setNome(linha["especialidade_nome"])

        medico = Medico()
        medico.setId(int(linha["medico_id"]))
        medico.setNome(linha["medico_nome"])
        medico.setCrm(linha["medico_crm"])
        medico.setUfCrm(linha["medico_uf_crm"])
        medico.setEspecialidade(especialidade)
        medico.setSituacao(Situacao(linha["medico_situacao"]))

        ausencia = Ausencia()
        ausencia.setId(int(linha["id"]))
        ausencia.setMedico(medico)
        ausencia.setMotivo(linha["motivo"])
        data_inicial = Ausencia._converter_data(linha["data_inicial"])
        if data_inicial is not None:
            ausencia.setDataInicial(data_inicial)
        data_final = Ausencia._converter_data(linha["data_final"])
        if data_final is not None:
            ausencia.setDataFinal(data_final)
        return ausencia

    @staticmethod
    def listarFuturasPorMedico(medicoId: int) -> List[Ausencia]:
        hoje = Ausencia._agora_clinica().date()
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT a.id, a.motivo, a.data_inicial, a.data_final,
                       m.id AS medico_id, m.nome AS medico_nome, m.crm AS medico_crm,
                       m.uf_crm AS medico_uf_crm, m.situacao AS medico_situacao,
                       e.id AS especialidade_id, e.nome AS especialidade_nome
                FROM ausencias a
                INNER JOIN medicos m ON m.id = a.medico_id
                INNER JOIN especialidades e ON e.id = m.especialidade_id
                WHERE a.medico_id = %s
                  AND a.data_final >= %s
                ORDER BY a.data_inicial ASC, a.data_final ASC
                """,
                (medicoId, hoje),
            )
            linhas = cursor.fetchall()
            cursor.close()
            return [Ausencia._montar_ausencia(linha) for linha in linhas]
        finally:
            conexao.close()

    @staticmethod
    def existeAusenciaNaData(medicoId: int, data: date) -> bool:
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor()
            cursor.execute(
                """
                SELECT 1
                FROM ausencias
                WHERE medico_id = %s
                  AND data_inicial <= %s
                  AND data_final >= %s
                LIMIT 1
                """,
                (medicoId, data, data),
            )
            existe = cursor.fetchone() is not None
            cursor.close()
            return existe
        finally:
            conexao.close()

    def salvar(self) -> bool:
        if (
            self.__medico is None
            or self.__medico.getId() is None
            or not (self.__motivo or "").strip()
            or self.__dataInicial is None
            or self.__dataFinal is None
        ):
            raise ValueError(
                "Médico, motivo, data inicial e data final são obrigatórios para a ausência."
            )

        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor()
            # UC11 só registra ausências novas; não há edição de ausência nos requisitos.
            cursor.execute(
                """
                INSERT INTO ausencias (medico_id, motivo, data_inicial, data_final)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    self.__medico.getId(),
                    self.__motivo,
                    self.__dataInicial,
                    self.__dataFinal,
                ),
            )
            self.__id = int(cursor.lastrowid)
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
            "medico": self.__medico.to_dict() if self.__medico else None,
            "motivo": self.__motivo,
            "dataInicial": self.__dataInicial.isoformat() if self.__dataInicial else None,
            "dataFinal": self.__dataFinal.isoformat() if self.__dataFinal else None,
        }
