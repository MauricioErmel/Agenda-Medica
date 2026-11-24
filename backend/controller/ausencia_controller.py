from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

import config
from model.ausencia import Ausencia
from model.consulta import Consulta
from model.medico import Medico
from model.situacao import Situacao


class AusenciaController:
    """Controlador de registro de ausências médicas — UC11 (RN06, RN10)."""

    @staticmethod
    def _agora_clinica() -> datetime:
        return config.agora_clinica()

    def listarAusenciasFuturas(self, medicoId: int) -> List[Ausencia]:
        if not isinstance(medicoId, int) or isinstance(medicoId, bool) or medicoId <= 0:
            return []
        return Ausencia.listarFuturasPorMedico(medicoId)

    def validarAusencia(
        self,
        medicoId: int,
        motivo: str,
        dataInicial: Optional[date],
        dataFinal: Optional[date],
    ) -> Optional[str]:
        if not isinstance(medicoId, int) or isinstance(medicoId, bool) or medicoId <= 0:
            return "Dados inválidos para registro de ausência"

        medico = Medico.buscarPorId(medicoId)
        situacao = medico.getSituacao() if medico is not None else None
        motivo_limpo = (motivo or "").strip()
        hoje = self._agora_clinica().date()

        datas_validas = (
            isinstance(dataInicial, date)
            and not isinstance(dataInicial, datetime)
            and isinstance(dataFinal, date)
            and not isinstance(dataFinal, datetime)
        )

        if (
            medico is None
            or situacao != Situacao.ATIVO
            or not motivo_limpo
            or not datas_validas
            or dataInicial < hoje
            or dataFinal < dataInicial
        ):
            return "Dados inválidos para registro de ausência"

        existeConsulta = Consulta.existeFuturaPorMedicoNoPeriodo(medicoId, dataInicial, dataFinal)
        if existeConsulta:
            return "Existem consultas futuras agendadas no período; cancele-as antes (UC9)"

        return None

    def registrarAusencia(
        self,
        medicoId: int,
        motivo: str,
        dataInicial: Optional[date],
        dataFinal: Optional[date],
    ) -> str:
        erro = self.validarAusencia(medicoId, motivo, dataInicial, dataFinal)
        if erro is not None:
            return erro

        medico = Medico.buscarPorId(medicoId)
        if medico is None:
            return "Dados inválidos para registro de ausência"

        novaAusencia = Ausencia()
        novaAusencia.setMedico(medico)
        novaAusencia.setMotivo((motivo or "").strip())
        novaAusencia.setDataInicial(dataInicial)
        novaAusencia.setDataFinal(dataFinal)
        novaAusencia.salvar()
        return "Ausência registrada com sucesso!"
