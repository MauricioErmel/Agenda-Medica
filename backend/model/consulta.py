from __future__ import annotations

from datetime import date, datetime, time
from typing import List, Optional

import config
from database import Database
from model.especialidade import Especialidade
from model.medico import Medico
from model.paciente import Paciente
from model.sexo import Sexo
from model.situacao import Situacao
from model.status_consulta import StatusConsulta
from model.status_lembrete import StatusLembrete


class Consulta:
    """Entidade Consulta conforme Diagrama de Classes (v3) — Ciclo 3."""

    def __init__(self) -> None:
        self.__id: Optional[int] = None
        self.__paciente: Optional[Paciente] = None
        self.__medico: Optional[Medico] = None
        self.__dataHora: Optional[datetime] = None
        self.__status: Optional[StatusConsulta] = None
        self.__lembrete: Optional[StatusLembrete] = None
        self.__motivoCancelamento: Optional[str] = None

    def getId(self) -> Optional[int]:
        return self.__id

    def setId(self, id: int) -> None:
        self.__id = id

    def getPaciente(self) -> Optional[Paciente]:
        return self.__paciente

    def setPaciente(self, paciente: Paciente) -> None:
        if paciente is None:
            raise ValueError("Paciente é obrigatório para a consulta (multiplicidade 1).")
        self.__paciente = paciente

    def getMedico(self) -> Optional[Medico]:
        return self.__medico

    def setMedico(self, medico: Medico) -> None:
        if medico is None:
            raise ValueError("Médico é obrigatório para a consulta (multiplicidade 1).")
        self.__medico = medico

    def getDataHora(self) -> Optional[datetime]:
        return self.__dataHora

    def setDataHora(self, dataHora: datetime) -> None:
        self.__dataHora = dataHora

    def getStatus(self) -> Optional[StatusConsulta]:
        return self.__status

    def setStatus(self, status: StatusConsulta) -> None:
        self.__status = status

    def getLembrete(self) -> Optional[StatusLembrete]:
        return self.__lembrete

    def setLembrete(self, lembrete: StatusLembrete) -> None:
        self.__lembrete = lembrete

    def getMotivoCancelamento(self) -> Optional[str]:
        return self.__motivoCancelamento

    def setMotivoCancelamento(self, motivo: Optional[str]) -> None:
        self.__motivoCancelamento = motivo

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
    def _converter_data_hora(valor: object) -> Optional[datetime]:
        if isinstance(valor, datetime):
            return valor.replace(tzinfo=None) if valor.tzinfo is not None else valor
        if isinstance(valor, str):
            texto = valor.strip()
            if not texto:
                return None
            try:
                dt = datetime.fromisoformat(texto)
                return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt
            except ValueError:
                return None
        return None

    @staticmethod
    def _montar_consulta(linha: dict) -> Consulta:
        paciente = Paciente()
        paciente.setId(int(linha["paciente_id"]))
        paciente.setCpf(linha["paciente_cpf"])
        paciente.setNome(linha["paciente_nome"])
        data_nasc = Consulta._converter_data(linha["paciente_data_nascimento"])
        if data_nasc is not None:
            paciente.setDataNascimento(data_nasc)
        paciente.setSexo(Sexo(linha["paciente_sexo"]))
        paciente.setTelefone(linha["paciente_telefone"])
        paciente.setSituacao(Situacao(linha["paciente_situacao"]))

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

        consulta = Consulta()
        consulta.setId(int(linha["id"]))
        consulta.setPaciente(paciente)
        consulta.setMedico(medico)
        data_hora = Consulta._converter_data_hora(linha["data_hora"])
        if data_hora is not None:
            consulta.setDataHora(data_hora)
        consulta.setStatus(StatusConsulta(linha["status"]))
        consulta.setLembrete(StatusLembrete(linha["lembrete"]))
        if linha.get("motivo_cancelamento") is not None:
            consulta.setMotivoCancelamento(linha["motivo_cancelamento"])
        return consulta

    @staticmethod
    def listarHorariosOcupados(medicoId: int, data: date) -> List[time]:
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT data_hora
                FROM consultas
                WHERE medico_id = %s
                  AND DATE(data_hora) = %s
                  AND status = %s
                ORDER BY data_hora ASC
                """,
                (medicoId, data, StatusConsulta.AGENDADA.value),
            )
            linhas = cursor.fetchall()
            cursor.close()
            horarios: List[time] = []
            for linha in linhas:
                dt = Consulta._converter_data_hora(linha["data_hora"])
                if dt is not None:
                    horarios.append(dt.time().replace(second=0, microsecond=0))
            return horarios
        finally:
            conexao.close()

    @staticmethod
    def existeConflitoPaciente(pacienteId: int, dataHora: datetime) -> bool:
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor()
            cursor.execute(
                """
                SELECT 1
                FROM consultas
                WHERE paciente_id = %s
                  AND data_hora = %s
                  AND status = %s
                LIMIT 1
                """,
                (pacienteId, dataHora, StatusConsulta.AGENDADA.value),
            )
            existe = cursor.fetchone() is not None
            cursor.close()
            return existe
        finally:
            conexao.close()

    @staticmethod
    def listarFuturasAgendadasPorPaciente(pacienteId: int) -> List[Consulta]:
        agora = Consulta._agora_clinica()
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT c.id, c.data_hora, c.status, c.lembrete, c.motivo_cancelamento,
                       p.id AS paciente_id, p.cpf AS paciente_cpf, p.nome AS paciente_nome,
                       p.data_nascimento AS paciente_data_nascimento, p.sexo AS paciente_sexo,
                       p.telefone AS paciente_telefone, p.situacao AS paciente_situacao,
                       m.id AS medico_id, m.nome AS medico_nome, m.crm AS medico_crm,
                       m.uf_crm AS medico_uf_crm, m.situacao AS medico_situacao,
                       e.id AS especialidade_id, e.nome AS especialidade_nome
                FROM consultas c
                INNER JOIN pacientes p ON p.id = c.paciente_id
                INNER JOIN medicos m ON m.id = c.medico_id
                INNER JOIN especialidades e ON e.id = m.especialidade_id
                WHERE c.paciente_id = %s
                  AND c.status = %s
                  AND c.data_hora > %s
                ORDER BY c.data_hora ASC
                """,
                (pacienteId, StatusConsulta.AGENDADA.value, agora),
            )
            linhas = cursor.fetchall()
            cursor.close()
            return [Consulta._montar_consulta(linha) for linha in linhas]
        finally:
            conexao.close()

    @staticmethod
    def existeFuturaPorMedico(medicoId: int) -> bool:
        agora = Consulta._agora_clinica()
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor()
            cursor.execute(
                """
                SELECT 1
                FROM consultas
                WHERE medico_id = %s
                  AND status = %s
                  AND data_hora > %s
                LIMIT 1
                """,
                (medicoId, StatusConsulta.AGENDADA.value, agora),
            )
            existe = cursor.fetchone() is not None
            cursor.close()
            return existe
        finally:
            conexao.close()

    @staticmethod
    def existeFuturaPorMedicoNoPeriodo(medicoId: int, dataInicial: date, dataFinal: date) -> bool:
        agora = Consulta._agora_clinica()
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor()
            cursor.execute(
                """
                SELECT 1
                FROM consultas
                WHERE medico_id = %s
                  AND status = %s
                  AND data_hora > %s
                  AND DATE(data_hora) >= %s
                  AND DATE(data_hora) <= %s
                LIMIT 1
                """,
                (medicoId, StatusConsulta.AGENDADA.value, agora, dataInicial, dataFinal),
            )
            existe = cursor.fetchone() is not None
            cursor.close()
            return existe
        finally:
            conexao.close()

    @staticmethod
    def listarLembretesPendentes() -> List[Consulta]:
        agora = Consulta._agora_clinica()
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT c.id, c.data_hora, c.status, c.lembrete, c.motivo_cancelamento,
                       p.id AS paciente_id, p.cpf AS paciente_cpf, p.nome AS paciente_nome,
                       p.data_nascimento AS paciente_data_nascimento, p.sexo AS paciente_sexo,
                       p.telefone AS paciente_telefone, p.situacao AS paciente_situacao,
                       m.id AS medico_id, m.nome AS medico_nome, m.crm AS medico_crm,
                       m.uf_crm AS medico_uf_crm, m.situacao AS medico_situacao,
                       e.id AS especialidade_id, e.nome AS especialidade_nome
                FROM consultas c
                INNER JOIN pacientes p ON p.id = c.paciente_id
                INNER JOIN medicos m ON m.id = c.medico_id
                INNER JOIN especialidades e ON e.id = m.especialidade_id
                WHERE c.status = %s
                  AND c.lembrete = %s
                  AND c.data_hora > %s
                ORDER BY c.data_hora ASC
                """,
                (StatusConsulta.AGENDADA.value, StatusLembrete.PENDENTE.value, agora),
            )
            linhas = cursor.fetchall()
            cursor.close()
            return [Consulta._montar_consulta(linha) for linha in linhas]
        finally:
            conexao.close()

    def isLembretePendente(self) -> bool:
        return (
            self.__status == StatusConsulta.AGENDADA
            and self.__lembrete == StatusLembrete.PENDENTE
            and self.__dataHora is not None
            and self.__dataHora > self._agora_clinica()
        )

    @staticmethod
    def buscarPorId(id: int) -> Optional[Consulta]:
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT c.id, c.data_hora, c.status, c.lembrete, c.motivo_cancelamento,
                       p.id AS paciente_id, p.cpf AS paciente_cpf, p.nome AS paciente_nome,
                       p.data_nascimento AS paciente_data_nascimento, p.sexo AS paciente_sexo,
                       p.telefone AS paciente_telefone, p.situacao AS paciente_situacao,
                       m.id AS medico_id, m.nome AS medico_nome, m.crm AS medico_crm,
                       m.uf_crm AS medico_uf_crm, m.situacao AS medico_situacao,
                       e.id AS especialidade_id, e.nome AS especialidade_nome
                FROM consultas c
                INNER JOIN pacientes p ON p.id = c.paciente_id
                INNER JOIN medicos m ON m.id = c.medico_id
                INNER JOIN especialidades e ON e.id = m.especialidade_id
                WHERE c.id = %s
                LIMIT 1
                """,
                (id,),
            )
            linha = cursor.fetchone()
            cursor.close()
            if not linha:
                return None
            return Consulta._montar_consulta(linha)
        finally:
            conexao.close()

    def salvar(self) -> bool:
        if (
            self.__paciente is None
            or self.__paciente.getId() is None
            or self.__medico is None
            or self.__medico.getId() is None
            or self.__dataHora is None
            or self.__status is None
            or self.__lembrete is None
        ):
            raise ValueError(
                "Paciente, médico, data/hora, status e lembrete são obrigatórios para a consulta."
            )

        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor()
            if self.__id is None:
                cursor.execute(
                    """
                    INSERT INTO consultas (
                        paciente_id, medico_id, data_hora, status, lembrete, motivo_cancelamento
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.__paciente.getId(),
                        self.__medico.getId(),
                        self.__dataHora,
                        self.__status.value,
                        self.__lembrete.value,
                        self.__motivoCancelamento,
                    ),
                )
                self.__id = int(cursor.lastrowid)
            else:
                cursor.execute(
                    """
                    UPDATE consultas
                    SET status = %s, lembrete = %s, motivo_cancelamento = %s
                    WHERE id = %s
                    """,
                    (
                        self.__status.value,
                        self.__lembrete.value,
                        self.__motivoCancelamento,
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
            "paciente": self.__paciente.to_dict() if self.__paciente else None,
            "medico": self.__medico.to_dict() if self.__medico else None,
            "dataHora": self.__dataHora.strftime("%Y-%m-%dT%H:%M") if self.__dataHora else None,
            "status": self.__status.value if self.__status else None,
            "lembrete": self.__lembrete.value if self.__lembrete else None,
            "motivoCancelamento": self.__motivoCancelamento,
        }
