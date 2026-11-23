from __future__ import annotations

from datetime import time, timedelta
from typing import Optional

from model.dia_semana import DiaSemana


class GradeAtendimento:
    """Entidade GradeAtendimento conforme Diagrama de Classes (v2) — Ciclo 2."""

    def __init__(self) -> None:
        self.__id: Optional[int] = None
        self.__diaSemana: Optional[DiaSemana] = None
        self.__horaInicial: Optional[time] = None
        self.__horaFinal: Optional[time] = None

    def getId(self) -> Optional[int]:
        return self.__id

    def setId(self, id: int) -> None:
        self.__id = id

    def getDiaSemana(self) -> Optional[DiaSemana]:
        return self.__diaSemana

    def setDiaSemana(self, diaSemana: DiaSemana) -> None:
        self.__diaSemana = diaSemana

    def getHoraInicial(self) -> Optional[time]:
        return self.__horaInicial

    def setHoraInicial(self, horaInicial: time) -> None:
        self.__horaInicial = horaInicial

    def getHoraFinal(self) -> Optional[time]:
        return self.__horaFinal

    def setHoraFinal(self, horaFinal: time) -> None:
        self.__horaFinal = horaFinal

    def isHorarioValido(self) -> bool:
        if (
            self.__diaSemana is None
            or self.__horaInicial is None
            or self.__horaFinal is None
        ):
            return False
        return self.__horaFinal > self.__horaInicial

    @staticmethod
    def _converter_horario(valor: object) -> Optional[time]:
        if isinstance(valor, time):
            return valor
        if isinstance(valor, timedelta):
            total_segundos = int(valor.total_seconds())
            if total_segundos < 0 or total_segundos >= 86400:
                return None
            horas, resto = divmod(total_segundos, 3600)
            minutos, segundos = divmod(resto, 60)
            return time(horas, minutos, segundos)
        if isinstance(valor, str):
            texto = valor.strip()
            if not texto:
                return None
            try:
                partes = texto.split(":")
                if len(partes) == 2:
                    return time(int(partes[0]), int(partes[1]))
                if len(partes) == 3:
                    return time(int(partes[0]), int(partes[1]), int(partes[2]))
            except ValueError:
                return None
        return None

    @staticmethod
    def _montar_grade(linha: dict) -> GradeAtendimento:
        grade = GradeAtendimento()
        grade.setId(int(linha["id"]))
        grade.setDiaSemana(DiaSemana(linha["dia_semana"]))
        hora_inicial = GradeAtendimento._converter_horario(linha["hora_inicial"])
        hora_final = GradeAtendimento._converter_horario(linha["hora_final"])
        if hora_inicial is not None:
            grade.setHoraInicial(hora_inicial)
        if hora_final is not None:
            grade.setHoraFinal(hora_final)
        return grade

    def to_dict(self) -> dict:
        return {
            "id": self.__id,
            "diaSemana": self.__diaSemana.value if self.__diaSemana else None,
            "horaInicial": self.__horaInicial.strftime("%H:%M") if self.__horaInicial else None,
            "horaFinal": self.__horaFinal.strftime("%H:%M") if self.__horaFinal else None,
        }
