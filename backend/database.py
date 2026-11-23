import mysql.connector
from mysql.connector.connection import MySQLConnection

import config


class Database:
    """Gerencia conexões com o banco de dados MySQL."""

    @staticmethod
    def get_connection(incluir_banco: bool = True) -> MySQLConnection:
        parametros = {
            "host": config.DB_HOST,
            "port": config.DB_PORT,
            "user": config.DB_USER,
            "password": config.DB_PASSWORD,
            "charset": "utf8mb4",
            "collation": "utf8mb4_unicode_ci",
            "autocommit": False,
        }
        if incluir_banco:
            parametros["database"] = config.DB_NAME
        return mysql.connector.connect(**parametros)
