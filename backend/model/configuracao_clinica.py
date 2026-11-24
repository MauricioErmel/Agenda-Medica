from __future__ import annotations

import config


class ConfiguracaoClinica:
    """Configurações da clínica (RNF04) conforme Diagrama de Classes (v4) — Ciclo 4."""

    def __init__(self) -> None:
        self.__nomeClinica: str = config.CLINICA_NOME
        self.__telefoneClinica: str = config.CLINICA_TELEFONE
        self.__duracaoConsultaMinutos: int = config.CONSULTA_DURACAO_MINUTOS

    def getNomeClinica(self) -> str:
        return self.__nomeClinica

    def getTelefoneClinica(self) -> str:
        return self.__telefoneClinica

    def getDuracaoConsultaMinutos(self) -> int:
        return self.__duracaoConsultaMinutos

    @staticmethod
    def obter() -> ConfiguracaoClinica:
        return ConfiguracaoClinica()

    def to_dict(self) -> dict:
        return {
            "nomeClinica": self.__nomeClinica,
            "telefoneClinica": self.__telefoneClinica,
            "duracaoConsultaMinutos": self.__duracaoConsultaMinutos,
        }
