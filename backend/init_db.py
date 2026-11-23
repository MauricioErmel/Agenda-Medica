"""Script utilitário para criar o banco de dados, tabelas e administrador inicial."""

from pathlib import Path

from database import Database


def _separar_comandos_sql(sql: str) -> list[str]:
    linhas_sem_comentarios = [
        linha
        for linha in sql.splitlines()
        if not linha.strip().startswith("--")
    ]
    conteudo = "\n".join(linhas_sem_comentarios)
    return [cmd.strip() for cmd in conteudo.split(";") if cmd.strip()]


def inicializar_banco() -> None:
    schema_path = Path(__file__).resolve().parent.parent / "database" / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    comandos = _separar_comandos_sql(sql)

    conexao = Database.get_connection(incluir_banco=False)
    try:
        cursor = conexao.cursor()
        for comando in comandos:
            cursor.execute(comando)
        conexao.commit()
        cursor.close()
        print("Banco de dados 'agenda_medica' inicializado com sucesso!")
        print("Administrador padrão disponível: login 'admin' / senha 'admin123'")
    finally:
        conexao.close()


if __name__ == "__main__":
    inicializar_banco()
