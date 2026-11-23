from __future__ import annotations

from typing import List, Optional

from model.especialidade import Especialidade
from model.grade_atendimento import GradeAtendimento
from model.medico import Medico
from model.situacao import Situacao

_UFS_BRASIL = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}


class MedicoController:
    """Controlador de gestão de médicos — CU4 e CU5."""

    def _validar_estrutura_grades(self, grades: List[GradeAtendimento]) -> bool:
        if not isinstance(grades, list):
            return False

        # Loop conforme CU4 e CU5: pergunta a cada grade se o horário é válido
        todos_horarios_validos = True
        dias_vistos = set()
        for grade in grades:
            if not isinstance(grade, GradeAtendimento):
                todos_horarios_validos = False
                continue
            if not grade.isHorarioValido():
                todos_horarios_validos = False
            dia = grade.getDiaSemana()
            if dia is None or dia in dias_vistos:
                todos_horarios_validos = False
            else:
                dias_vistos.add(dia)

        if len(grades) == 0 or len(grades) > 7:
            return False
        return todos_horarios_validos

    def listarEspecialidades(self) -> List[Especialidade]:
        return Especialidade.listarTodas()

    def cadastrarMedico(
        self,
        nome: str,
        crm: str,
        ufCrm: str,
        especialidadeId: int,
        grades: List[GradeAtendimento],
    ) -> str:
        grades_validas = self._validar_estrutura_grades(grades)

        nome_limpo = (nome or "").strip()
        crm_limpo = (crm or "").strip()
        uf_limpa = (ufCrm or "").strip().upper()

        if (
            not nome_limpo
            or not crm_limpo
            or uf_limpa not in _UFS_BRASIL
            or not isinstance(especialidadeId, int)
            or isinstance(especialidadeId, bool)
            or especialidadeId <= 0
            or not grades_validas
        ):
            return "Dados inválidos ou grade incoerente"

        if Medico.existeCrmUf(crm_limpo, uf_limpa, 0):
            return "CRM já cadastrado no sistema"

        especialidade = Especialidade.buscarPorId(especialidadeId)
        if especialidade is None:
            return "Dados inválidos ou grade incoerente"

        novoMedico = Medico()
        novoMedico.setNome(nome_limpo)
        novoMedico.setCrm(crm_limpo)
        novoMedico.setUfCrm(uf_limpa)
        novoMedico.setEspecialidade(especialidade)
        novoMedico.setSituacao(Situacao.ATIVO)
        novoMedico.setGrades(grades)
        novoMedico.salvar()

        return "Médico cadastrado com sucesso!"

    def listarMedicos(self) -> List[Medico]:
        return Medico.listarTodos()

    def buscarMedico(self, id: int) -> Optional[Medico]:
        if not isinstance(id, int) or isinstance(id, bool) or id <= 0:
            return None
        return Medico.buscarPorId(id)

    def validarMedico(
        self,
        id: int,
        nome: str,
        crm: str,
        ufCrm: str,
        especialidadeId: int,
        grades: List[GradeAtendimento],
        situacao: Situacao,
    ) -> Optional[str]:
        grades_validas = self._validar_estrutura_grades(grades)

        nome_limpo = (nome or "").strip()
        crm_limpo = (crm or "").strip()
        uf_limpa = (ufCrm or "").strip().upper()

        if (
            not isinstance(id, int)
            or isinstance(id, bool)
            or id <= 0
            or not nome_limpo
            or not crm_limpo
            or uf_limpa not in _UFS_BRASIL
            or not isinstance(especialidadeId, int)
            or isinstance(especialidadeId, bool)
            or especialidadeId <= 0
            or not isinstance(situacao, Situacao)
            or not grades_validas
        ):
            return "Dados inválidos ou grade incoerente"

        if Medico.existeCrmUf(crm_limpo, uf_limpa, id):
            return "CRM já cadastrado no sistema"

        # Pendência planejada (Ciclo 3): validar RN08 (consultas futuras Agendadas)
        # ao alterar grade ou inativar médico.
        return None

    def editarMedico(
        self,
        id: int,
        nome: str,
        crm: str,
        ufCrm: str,
        especialidadeId: int,
        grades: List[GradeAtendimento],
        situacao: Situacao,
    ) -> str:
        erro = self.validarMedico(id, nome, crm, ufCrm, especialidadeId, grades, situacao)
        if erro is not None:
            return erro

        medico = Medico.buscarPorId(id)
        if medico is None:
            return "Dados inválidos ou grade incoerente"

        especialidade = Especialidade.buscarPorId(especialidadeId)
        if especialidade is None:
            return "Dados inválidos ou grade incoerente"

        medico.setNome((nome or "").strip())
        medico.setCrm((crm or "").strip())
        medico.setUfCrm((ufCrm or "").strip().upper())
        medico.setEspecialidade(especialidade)
        medico.setGrades(grades)
        medico.setSituacao(situacao)
        medico.salvar()

        return "Médico atualizado com sucesso!"
