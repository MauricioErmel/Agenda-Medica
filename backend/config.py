import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def _carregar_env() -> None:
    """Carrega variáveis de ambiente do arquivo backend/.env se existir."""
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for linha in env_path.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")
        os.environ.setdefault(chave, valor)


_carregar_env()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "agenda_medica")

SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

CLINICA_NOME = os.getenv("CLINICA_NOME", "Clínica Vida Saudável")
CLINICA_TELEFONE = os.getenv("CLINICA_TELEFONE", "(51) 3333-4444")
CONSULTA_DURACAO_MINUTOS = int(os.getenv("CONSULTA_DURACAO_MINUTOS", "30"))
TIMEZONE = os.getenv("TIMEZONE", "America/Sao_Paulo")


def agora_clinica() -> datetime:
    """Data e hora atuais no fuso da clínica (RNF03), sem tzinfo."""
    try:
        return datetime.now(ZoneInfo(TIMEZONE)).replace(tzinfo=None)
    except ZoneInfoNotFoundError:
        if TIMEZONE == "America/Sao_Paulo":
            return datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)
        return datetime.now()
