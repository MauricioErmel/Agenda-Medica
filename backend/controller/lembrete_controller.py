from __future__ import annotations

import re
from typing import List, Optional
from urllib.parse import quote

from model.configuracao_clinica import ConfiguracaoClinica
from model.consulta import Consulta
from model.medico import Medico
from model.paciente import Paciente
from model.status_lembrete import StatusLembrete


class LembreteController:
    """Controlador de envio de lembretes via WhatsApp — UC10 (RN09, RNF04)."""

    @staticmethod
    def _normalizar_telefone_whatsapp(telefone: str) -> str:
        digitos = re.sub(r"\D", "", telefone or "")
        if len(digitos) in (10, 11) and not digitos.startswith("55"):
            return f"55{digitos}"
        return digitos

    @staticmethod
    def _montar_mensagem_padrao(
        nome_paciente: str,
        nome_clinica: str,
        nome_medico: str,
        data_hora_texto: str,
        telefone_clinica: str,
    ) -> str:
        return (
            f"{nome_paciente}, você possui uma consulta agendada na {nome_clinica} "
            f"com {nome_medico} em {data_hora_texto}.\n"
            f"Caso você não possa comparecer, por favor, avise a clínica pelo telefone "
            f"{telefone_clinica} para cancelar o agendamento.\n"
            f"Se você for comparecer, não precisa fazer nada. Seu médico estará te aguardando."
        )

    def listarLembretesPendentes(self) -> List[Consulta]:
        return Consulta.listarLembretesPendentes()

    def gerarLinkWhatsApp(self, consultaId: int) -> Optional[str]:
        if not isinstance(consultaId, int) or isinstance(consultaId, bool) or consultaId <= 0:
            return None

        consulta = Consulta.buscarPorId(consultaId)
        pendente = consulta.isLembretePendente() if consulta is not None else False
        if consulta is None or not pendente:
            return None

        config_clinica = ConfiguracaoClinica.obter()
        nomeClinica = config_clinica.getNomeClinica()
        telefoneClinica = config_clinica.getTelefoneClinica()

        paciente: Optional[Paciente] = consulta.getPaciente()
        nomePaciente = paciente.getNome() if paciente is not None else ""
        telefonePaciente = paciente.getTelefone() if paciente is not None else ""

        medico: Optional[Medico] = consulta.getMedico()
        dataHora = consulta.getDataHora()
        nomeMedico = medico.getNome() if medico is not None else ""

        data_hora_texto = (
            f"{dataHora.strftime('%d/%m/%Y')} às {dataHora.strftime('%H:%M')}"
            if dataHora is not None
            else ""
        )
        mensagem = self._montar_mensagem_padrao(
            nomePaciente,
            nomeClinica,
            nomeMedico,
            data_hora_texto,
            telefoneClinica,
        )
        numero_wa = self._normalizar_telefone_whatsapp(telefonePaciente)
        return f"https://wa.me/{numero_wa}?text={quote(mensagem, safe='')}"

    def confirmarEnvio(self, consultaId: int) -> str:
        if not isinstance(consultaId, int) or isinstance(consultaId, bool) or consultaId <= 0:
            return "Consulta não elegível para lembrete"

        consulta = Consulta.buscarPorId(consultaId)
        pendente = consulta.isLembretePendente() if consulta is not None else False
        if consulta is None or not pendente:
            return "Consulta não elegível para lembrete"

        consulta.setLembrete(StatusLembrete.ENVIADO)
        consulta.salvar()
        return "Lembrete marcado como enviado!"
