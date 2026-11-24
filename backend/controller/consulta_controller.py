from __future__ import annotations

from datetime import date, datetime, time
from typing import List, Optional

import config
from model.ausencia import Ausencia
from model.configuracao_clinica import ConfiguracaoClinica
from model.consulta import Consulta
from model.grade_atendimento import GradeAtendimento
from model.medico import Medico
from model.paciente import Paciente
from model.situacao import Situacao
from model.status_consulta import StatusConsulta
from model.status_lembrete import StatusLembrete


class ConsultaController:
    """Controlador de agendamento e cancelamento de consultas — UC8 e UC9."""

    @staticmethod
    def _agora_clinica() -> datetime:
        return config.agora_clinica()

    def verificarPaciente(self, pacienteId: int) -> Optional[str]:
        if not isinstance(pacienteId, int) or isinstance(pacienteId, bool) or pacienteId <= 0:
            return "Pacientes inativos não podem ser agendados"

        paciente = Paciente.buscarPorId(pacienteId)
        situacao = paciente.getSituacao() if paciente is not None else None
        if paciente is None or situacao == Situacao.INATIVO:
            return "Pacientes inativos não podem ser agendados"
        return None

    def listarMedicosAtivos(self) -> List[Medico]:
        return Medico.listarAtivos()

    def listarHorariosLivres(self, medicoId: int, data: date) -> List[time]:
        if (
            not isinstance(medicoId, int)
            or isinstance(medicoId, bool)
            or medicoId <= 0
            or not isinstance(data, date)
            or isinstance(data, datetime)
        ):
            return []

        medico = Medico.buscarPorId(medicoId)
        situacaoMed = medico.getSituacao() if medico is not None else None
        agora = self._agora_clinica()

        if medico is None or situacaoMed == Situacao.INATIVO or data < agora.date():
            return []

        ausente = Ausencia.existeAusenciaNaData(medicoId, data)
        if ausente:
            return []

        grade: Optional[GradeAtendimento] = medico.getGradeDoDia(data)
        if grade is None:
            return []

        config_clinica = ConfiguracaoClinica.obter()
        duracaoMinutos = config_clinica.getDuracaoConsultaMinutos()
        horariosGrade = grade.gerarHorarios(duracaoMinutos)
        ocupados = set(Consulta.listarHorariosOcupados(medicoId, data))

        # Mantém apenas horários futuros (RN06) que não estão ocupados (RN04, RN07).
        return [
            horario
            for horario in horariosGrade
            if horario not in ocupados and datetime.combine(data, horario) > agora
        ]

    def agendarConsulta(self, pacienteId: int, medicoId: int, dataHora: datetime) -> str:
        if not isinstance(dataHora, datetime):
            return "Horário indisponível"

        data_hora_limpa = (
            dataHora.replace(tzinfo=None) if dataHora.tzinfo is not None else dataHora
        )

        erroPaciente = self.verificarPaciente(pacienteId)
        if erroPaciente is not None:
            return erroPaciente

        horariosLivres = self.listarHorariosLivres(medicoId, data_hora_limpa.date())
        horario_escolhido = data_hora_limpa.time()
        if (
            data_hora_limpa.second != 0
            or data_hora_limpa.microsecond != 0
            or horario_escolhido not in horariosLivres
        ):
            return "Horário indisponível"

        conflitoPaciente = Consulta.existeConflitoPaciente(pacienteId, data_hora_limpa)
        if conflitoPaciente:
            return "Paciente já possui consulta agendada neste horário"

        paciente = Paciente.buscarPorId(pacienteId)
        medico = Medico.buscarPorId(medicoId)
        if paciente is None or medico is None:
            return "Horário indisponível"

        novaConsulta = Consulta()
        novaConsulta.setPaciente(paciente)
        novaConsulta.setMedico(medico)
        novaConsulta.setDataHora(data_hora_limpa)
        novaConsulta.setStatus(StatusConsulta.AGENDADA)
        novaConsulta.setLembrete(StatusLembrete.PENDENTE)
        novaConsulta.salvar()

        nomeMedico = medico.getNome()
        especialidade = medico.getEspecialidade()
        nomeEspecialidade = especialidade.getNome() if especialidade is not None else ""

        return (
            f"Consulta agendada com sucesso: "
            f"{data_hora_limpa.strftime('%d/%m/%Y')} às {data_hora_limpa.strftime('%H:%M')} "
            f"com {nomeMedico} ({nomeEspecialidade})"
        )

    def listarConsultasFuturasPaciente(self, pacienteId: int) -> List[Consulta]:
        if not isinstance(pacienteId, int) or isinstance(pacienteId, bool) or pacienteId <= 0:
            return []
        return Consulta.listarFuturasAgendadasPorPaciente(pacienteId)

    def cancelarConsulta(self, consultaId: int, motivo: str = "") -> str:
        if not isinstance(consultaId, int) or isinstance(consultaId, bool) or consultaId <= 0:
            return "Consulta não pode ser cancelada"

        consulta = Consulta.buscarPorId(consultaId)
        status = consulta.getStatus() if consulta is not None else None
        dataHora = consulta.getDataHora() if consulta is not None else None
        agora = self._agora_clinica()

        if (
            consulta is None
            or status != StatusConsulta.AGENDADA
            or dataHora is None
            or dataHora <= agora
        ):
            return "Consulta não pode ser cancelada"

        consulta.setStatus(StatusConsulta.CANCELADA)
        motivo_limpo = (motivo or "").strip()
        if motivo_limpo:
            consulta.setMotivoCancelamento(motivo_limpo)

        consulta.salvar()
        return "Consulta cancelada com sucesso!"
