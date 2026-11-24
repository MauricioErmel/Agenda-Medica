from __future__ import annotations

import re
from datetime import date, datetime
from typing import List, Optional

import config
from model.consulta import Consulta
from model.paciente import Paciente
from model.sexo import Sexo
from model.situacao import Situacao


class PacienteController:
    """Controlador de gestão de pacientes — UC6 e UC7."""

    @staticmethod
    def _hoje_clinica() -> date:
        return config.agora_clinica().date()

    @staticmethod
    def _rotulo_situacao(situacao: Optional[Situacao]) -> str:
        if situacao == Situacao.ATIVO:
            return "Ativo"
        if situacao == Situacao.INATIVO:
            return "Inativo"
        return ""

    def cadastrarPaciente(
        self,
        cpf: str,
        nome: str,
        dataNascimento: date,
        sexo: Sexo,
        telefone: str,
    ) -> str:
        cpf_limpo = re.sub(r"\D", "", cpf or "")
        nome_limpo = (nome or "").strip()
        telefone_limpo = (telefone or "").strip()

        if (
            len(cpf_limpo) != 11
            or not cpf_limpo.isdigit()
            or not nome_limpo
            or not isinstance(dataNascimento, date)
            or isinstance(dataNascimento, datetime)
            or dataNascimento > self._hoje_clinica()
            or not isinstance(sexo, Sexo)
            or not telefone_limpo
        ):
            return "Dados inválidos"

        existente = Paciente.buscarPorCpf(cpf_limpo)
        if existente is not None:
            nomeExistente = existente.getNome()
            situacaoExistente = existente.getSituacao()
            return (
                f"CPF já cadastrado no sistema: "
                f"{nomeExistente} ({self._rotulo_situacao(situacaoExistente)})"
            )

        novoPaciente = Paciente()
        novoPaciente.setCpf(cpf_limpo)
        novoPaciente.setNome(nome_limpo)
        novoPaciente.setDataNascimento(dataNascimento)
        novoPaciente.setSexo(sexo)
        novoPaciente.setTelefone(telefone_limpo)
        novoPaciente.setSituacao(Situacao.ATIVO)
        novoPaciente.salvar()

        return "Paciente cadastrado com sucesso!"

    def consultarPacientes(self, termo: str) -> List[Paciente]:
        termo_limpo = (termo or "").strip()
        if not termo_limpo:
            return []
        return Paciente.buscarPorFiltro(termo_limpo)

    def validarPaciente(
        self,
        id: int,
        nome: str,
        dataNascimento: date,
        sexo: Sexo,
        telefone: str,
        situacao: Situacao,
    ) -> Optional[str]:
        nome_limpo = (nome or "").strip()
        telefone_limpo = (telefone or "").strip()

        if (
            not isinstance(id, int)
            or isinstance(id, bool)
            or id <= 0
            or not nome_limpo
            or not isinstance(dataNascimento, date)
            or isinstance(dataNascimento, datetime)
            or dataNascimento > self._hoje_clinica()
            or not isinstance(sexo, Sexo)
            or not telefone_limpo
            or not isinstance(situacao, Situacao)
        ):
            return "Dados inválidos"

        if situacao == Situacao.INATIVO:
            futuras = Consulta.listarFuturasAgendadasPorPaciente(id)
            if futuras:
                return "Cancele antes as consultas futuras do paciente (UC9)"

        return None

    def editarPaciente(
        self,
        id: int,
        nome: str,
        dataNascimento: date,
        sexo: Sexo,
        telefone: str,
        situacao: Situacao,
    ) -> str:
        erro = self.validarPaciente(id, nome, dataNascimento, sexo, telefone, situacao)
        if erro is not None:
            return erro

        paciente = Paciente.buscarPorId(id)
        if paciente is None:
            return "Dados inválidos"

        paciente.setNome((nome or "").strip())
        paciente.setDataNascimento(dataNascimento)
        paciente.setSexo(sexo)
        paciente.setTelefone((telefone or "").strip())
        paciente.setSituacao(situacao)
        paciente.salvar()

        return "Dados do paciente atualizados com sucesso!"
