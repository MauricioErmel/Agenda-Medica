from __future__ import annotations

from typing import Dict, List, Optional

from database import Database
from model.dia_semana import DiaSemana
from model.especialidade import Especialidade
from model.grade_atendimento import GradeAtendimento
from model.situacao import Situacao


class Medico:
    """Entidade Medico conforme Diagrama de Classes (v2) — Ciclo 2."""

    _ORDEM_DIAS: Dict[DiaSemana, int] = {
        DiaSemana.SEGUNDA: 1,
        DiaSemana.TERCA: 2,
        DiaSemana.QUARTA: 3,
        DiaSemana.QUINTA: 4,
        DiaSemana.SEXTA: 5,
        DiaSemana.SABADO: 6,
        DiaSemana.DOMINGO: 7,
    }

    def __init__(self) -> None:
        self.__id: Optional[int] = None
        self.__nome: str = ""
        self.__crm: str = ""
        self.__ufCrm: str = ""
        self.__especialidade: Optional[Especialidade] = None
        self.__situacao: Optional[Situacao] = None
        self.__grades: List[GradeAtendimento] = []

    def getId(self) -> Optional[int]:
        return self.__id

    def setId(self, id: int) -> None:
        self.__id = id

    def getNome(self) -> str:
        return self.__nome

    def setNome(self, nome: str) -> None:
        self.__nome = nome

    def getCrm(self) -> str:
        return self.__crm

    def setCrm(self, crm: str) -> None:
        self.__crm = crm

    def getUfCrm(self) -> str:
        return self.__ufCrm

    def setUfCrm(self, ufCrm: str) -> None:
        self.__ufCrm = ufCrm

    def getEspecialidade(self) -> Optional[Especialidade]:
        return self.__especialidade

    def setEspecialidade(self, especialidade: Especialidade) -> None:
        if especialidade is None:
            raise ValueError("Especialidade é obrigatória para o médico (multiplicidade 1).")
        self.__especialidade = especialidade

    def getSituacao(self) -> Optional[Situacao]:
        return self.__situacao

    def setSituacao(self, situacao: Situacao) -> None:
        self.__situacao = situacao

    def getGrades(self) -> List[GradeAtendimento]:
        return list(self.__grades)

    def setGrades(self, grades: List[GradeAtendimento]) -> None:
        if not grades or len(grades) > 7:
            raise ValueError("A grade de atendimento deve conter entre 1 e 7 dias.")

        # Composição: Medico instancia e controla o ciclo de vida das suas grades
        grades_proprias: List[GradeAtendimento] = []
        dias_vistos = set()
        for item in grades:
            dia = item.getDiaSemana()
            if dia is None or dia in dias_vistos:
                raise ValueError("Cada dia da semana pode aparecer no máximo uma vez na grade.")
            dias_vistos.add(dia)

            copia = GradeAtendimento()
            if item.getId() is not None:
                copia.setId(item.getId())
            copia.setDiaSemana(dia)
            hora_inicial = item.getHoraInicial()
            hora_final = item.getHoraFinal()
            if hora_inicial is not None:
                copia.setHoraInicial(hora_inicial)
            if hora_final is not None:
                copia.setHoraFinal(hora_final)
            grades_proprias.append(copia)

        grades_proprias.sort(key=lambda g: self._ORDEM_DIAS.get(g.getDiaSemana(), 99))
        self.__grades = grades_proprias

    @staticmethod
    def _normalizar_crm(crm: str) -> str:
        return (crm or "").strip()

    @staticmethod
    def _normalizar_uf(ufCrm: str) -> str:
        return (ufCrm or "").strip().upper()

    @staticmethod
    def _montar_medico(linha: dict, grades: Optional[List[GradeAtendimento]] = None) -> Medico:
        medico = Medico()
        medico.setId(int(linha["id"]))
        medico.setNome(linha["nome"])
        medico.setCrm(linha["crm"])
        medico.setUfCrm(linha["uf_crm"])

        especialidade = Especialidade()
        especialidade.setId(int(linha["especialidade_id"]))
        especialidade.setNome(linha["especialidade_nome"])
        medico.setEspecialidade(especialidade)

        medico.setSituacao(Situacao(linha["situacao"]))
        if grades:
            medico.setGrades(grades)
        return medico

    @staticmethod
    def _buscar_grades_por_medicos(cursor, medico_ids: List[int]) -> Dict[int, List[GradeAtendimento]]:
        if not medico_ids:
            return {}
        marcadores = ", ".join(["%s"] * len(medico_ids))
        cursor.execute(
            f"""
            SELECT id, medico_id, dia_semana, hora_inicial, hora_final
            FROM grades_atendimento
            WHERE medico_id IN ({marcadores})
            ORDER BY FIELD(dia_semana, 'SEGUNDA', 'TERCA', 'QUARTA', 'QUINTA', 'SEXTA', 'SABADO', 'DOMINGO')
            """,
            tuple(medico_ids),
        )
        resultado: Dict[int, List[GradeAtendimento]] = {mid: [] for mid in medico_ids}
        for linha in cursor.fetchall():
            mid = int(linha["medico_id"])
            resultado[mid].append(GradeAtendimento._montar_grade(linha))
        return resultado

    @staticmethod
    def existeCrmUf(crm: str, ufCrm: str, ignorarId: int = 0) -> bool:
        crm_limpo = Medico._normalizar_crm(crm)
        uf_limpa = Medico._normalizar_uf(ufCrm)
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor()
            if ignorarId and ignorarId > 0:
                cursor.execute(
                    "SELECT 1 FROM medicos WHERE crm = %s AND uf_crm = %s AND id <> %s LIMIT 1",
                    (crm_limpo, uf_limpa, ignorarId),
                )
            else:
                cursor.execute(
                    "SELECT 1 FROM medicos WHERE crm = %s AND uf_crm = %s LIMIT 1",
                    (crm_limpo, uf_limpa),
                )
            existe = cursor.fetchone() is not None
            cursor.close()
            return existe
        finally:
            conexao.close()

    @staticmethod
    def listarTodos() -> List[Medico]:
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT m.id, m.nome, m.crm, m.uf_crm, m.especialidade_id,
                       e.nome AS especialidade_nome, m.situacao
                FROM medicos m
                INNER JOIN especialidades e ON e.id = m.especialidade_id
                ORDER BY m.nome ASC
                """
            )
            linhas = cursor.fetchall()
            medico_ids = [int(linha["id"]) for linha in linhas]
            grades_por_medico = Medico._buscar_grades_por_medicos(cursor, medico_ids)
            cursor.close()
            return [
                Medico._montar_medico(linha, grades_por_medico.get(int(linha["id"]), []))
                for linha in linhas
            ]
        finally:
            conexao.close()

    @staticmethod
    def buscarPorId(id: int) -> Optional[Medico]:
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT m.id, m.nome, m.crm, m.uf_crm, m.especialidade_id,
                       e.nome AS especialidade_nome, m.situacao
                FROM medicos m
                INNER JOIN especialidades e ON e.id = m.especialidade_id
                WHERE m.id = %s
                LIMIT 1
                """,
                (id,),
            )
            linha = cursor.fetchone()
            if not linha:
                cursor.close()
                return None
            grades_por_medico = Medico._buscar_grades_por_medicos(cursor, [int(linha["id"])])
            cursor.close()
            return Medico._montar_medico(linha, grades_por_medico.get(int(linha["id"]), []))
        finally:
            conexao.close()

    def salvar(self) -> bool:
        if (
            self.__especialidade is None
            or self.__especialidade.getId() is None
            or self.__situacao is None
            or not self.__grades
        ):
            raise ValueError("Especialidade, situação e ao menos uma grade são obrigatórias.")

        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor()
            if self.__id is None:
                cursor.execute(
                    """
                    INSERT INTO medicos (nome, crm, uf_crm, especialidade_id, situacao)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        self.__nome,
                        self.__crm,
                        self.__ufCrm,
                        self.__especialidade.getId(),
                        self.__situacao.value,
                    ),
                )
                self.__id = int(cursor.lastrowid)
            else:
                cursor.execute(
                    """
                    UPDATE medicos
                    SET nome = %s, crm = %s, uf_crm = %s, especialidade_id = %s, situacao = %s
                    WHERE id = %s
                    """,
                    (
                        self.__nome,
                        self.__crm,
                        self.__ufCrm,
                        self.__especialidade.getId(),
                        self.__situacao.value,
                        self.__id,
                    ),
                )
                cursor.execute(
                    "DELETE FROM grades_atendimento WHERE medico_id = %s",
                    (self.__id,),
                )

            for grade in self.__grades:
                cursor.execute(
                    """
                    INSERT INTO grades_atendimento (medico_id, dia_semana, hora_inicial, hora_final)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        self.__id,
                        grade.getDiaSemana().value,
                        grade.getHoraInicial().strftime("%H:%M:%S"),
                        grade.getHoraFinal().strftime("%H:%M:%S"),
                    ),
                )
                grade.setId(int(cursor.lastrowid))

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
            "nome": self.__nome,
            "crm": self.__crm,
            "ufCrm": self.__ufCrm,
            "especialidade": self.__especialidade.to_dict() if self.__especialidade else None,
            "situacao": self.__situacao.value if self.__situacao else None,
            "grades": [grade.to_dict() for grade in self.__grades],
        }
