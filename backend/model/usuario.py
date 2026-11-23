from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import List, Optional

from database import Database
from model.perfil import Perfil


class Usuario:
    """Entidade Usuario conforme Diagrama de Classes (v1) — Ciclo 1."""

    _HASH_ALGORITMO = "pbkdf2_sha256"
    _HASH_ITERACOES = 100_000

    def __init__(self) -> None:
        self.__id: Optional[int] = None
        self.__nome: str = ""
        self.__login: str = ""
        self.__senha: Optional[str] = None
        self.__perfil: Optional[Perfil] = None

    def getId(self) -> Optional[int]:
        return self.__id

    def setId(self, id: int) -> None:
        self.__id = id

    def getNome(self) -> str:
        return self.__nome

    def setNome(self, nome: str) -> None:
        self.__nome = nome

    def getLogin(self) -> str:
        return self.__login

    def setLogin(self, login: str) -> None:
        self.__login = login

    def setSenha(self, senha: str) -> None:
        self.__senha = self._gerar_hash_senha(senha)

    def getPerfil(self) -> Optional[Perfil]:
        return self.__perfil

    def setPerfil(self, perfil: Perfil) -> None:
        self.__perfil = perfil

    @classmethod
    def _gerar_hash_senha(cls, senha_plana: str) -> str:
        salt = secrets.token_bytes(16)
        derivada = hashlib.pbkdf2_hmac(
            "sha256",
            senha_plana.encode("utf-8"),
            salt,
            cls._HASH_ITERACOES,
        )
        return f"{cls._HASH_ALGORITMO}${cls._HASH_ITERACOES}${salt.hex()}${derivada.hex()}"

    @classmethod
    def _verificar_senha(cls, senha_plana: str, senha_armazenada: str) -> bool:
        try:
            algoritmo, iteracoes_str, salt_hex, hash_hex = senha_armazenada.split("$")
            if algoritmo != cls._HASH_ALGORITMO:
                return False
            iteracoes = int(iteracoes_str)
            salt = bytes.fromhex(salt_hex)
            derivada = hashlib.pbkdf2_hmac(
                "sha256",
                senha_plana.encode("utf-8"),
                salt,
                iteracoes,
            )
            return hmac.compare_digest(derivada.hex(), hash_hex)
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _montar_usuario(linha: dict) -> Usuario:
        usuario = Usuario()
        usuario.setId(int(linha["id"]))
        usuario.setNome(linha["nome"])
        usuario.setLogin(linha["login"])
        usuario.setPerfil(Perfil(linha["perfil"]))
        return usuario

    @staticmethod
    def autenticar(login: str, senha: str) -> Optional[Usuario]:
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, nome, login, senha, perfil FROM usuarios WHERE login = %s LIMIT 1",
                (login,),
            )
            linha = cursor.fetchone()
            cursor.close()
            if not linha:
                return None
            if not Usuario._verificar_senha(senha, linha["senha"]):
                return None
            return Usuario._montar_usuario(linha)
        finally:
            conexao.close()

    @staticmethod
    def existeLogin(login: str) -> bool:
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor()
            cursor.execute(
                "SELECT 1 FROM usuarios WHERE login = %s LIMIT 1",
                (login,),
            )
            existe = cursor.fetchone() is not None
            cursor.close()
            return existe
        finally:
            conexao.close()

    @staticmethod
    def listarRecepcionistas() -> List[Usuario]:
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, nome, login, perfil FROM usuarios WHERE perfil = %s ORDER BY nome ASC",
                (Perfil.RECEPCIONISTA.value,),
            )
            linhas = cursor.fetchall()
            cursor.close()
            return [Usuario._montar_usuario(linha) for linha in linhas]
        finally:
            conexao.close()

    @staticmethod
    def buscarPorId(id: int) -> Optional[Usuario]:
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, nome, login, perfil FROM usuarios WHERE id = %s LIMIT 1",
                (id,),
            )
            linha = cursor.fetchone()
            cursor.close()
            if not linha:
                return None
            return Usuario._montar_usuario(linha)
        finally:
            conexao.close()

    def salvar(self) -> bool:
        conexao = Database.get_connection()
        try:
            cursor = conexao.cursor()
            if self.__id is None:
                if not self.__senha or self.__perfil is None:
                    raise ValueError("Senha e perfil são obrigatórios para novo usuário.")
                cursor.execute(
                    "INSERT INTO usuarios (nome, login, senha, perfil) VALUES (%s, %s, %s, %s)",
                    (self.__nome, self.__login, self.__senha, self.__perfil.value),
                )
                self.__id = int(cursor.lastrowid)
            else:
                if self.__senha is not None:
                    cursor.execute(
                        "UPDATE usuarios SET nome = %s, senha = %s WHERE id = %s",
                        (self.__nome, self.__senha, self.__id),
                    )
                else:
                    cursor.execute(
                        "UPDATE usuarios SET nome = %s WHERE id = %s",
                        (self.__nome, self.__id),
                    )
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
            "login": self.__login,
            "perfil": self.__perfil.value if self.__perfil else None,
        }
