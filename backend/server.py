"""Servidor HTTP puro (http.server) da API Agenda Médica — Ciclo 1."""

from __future__ import annotations

import json
import mimetypes
import re
import secrets
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse

import config
from controller.auth_controller import AuthController
from controller.recepcionista_controller import RecepcionistaController
from model.perfil import Perfil

# Sessões ativas em memória: token -> dados públicos do usuário autenticado
SESSOES: Dict[str, dict] = {}

DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"


class AgendaMedicaHandler(BaseHTTPRequestHandler):
    auth_controller = AuthController()
    recepcionista_controller = RecepcionistaController()

    def _enviar_cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _enviar_json(self, status: int, payload: dict) -> None:
        corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self._enviar_cors()
        self.end_headers()
        self.wfile.write(corpo)

    def _ler_json(self) -> Optional[dict]:
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None
        if tamanho <= 0:
            return {}
        bruto = self.rfile.read(tamanho)
        try:
            dados = json.loads(bruto.decode("utf-8"))
            return dados if isinstance(dados, dict) else None
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

    def _obter_token(self) -> Optional[str]:
        cabecalho = self.headers.get("Authorization", "")
        if cabecalho.startswith("Bearer "):
            return cabecalho[7:].strip()
        return None

    def _usuario_autenticado(self) -> Optional[dict]:
        token = self._obter_token()
        if not token:
            return None
        return SESSOES.get(token)

    def _exigir_administrador(self) -> Optional[dict]:
        usuario = self._usuario_autenticado()
        if not usuario:
            self._enviar_json(
                HTTPStatus.UNAUTHORIZED,
                {"sucesso": False, "mensagem": "Usuário não autenticado"},
            )
            return None
        if usuario.get("perfil") != Perfil.ADMINISTRADOR.value:
            self._enviar_json(
                HTTPStatus.FORBIDDEN,
                {"sucesso": False, "mensagem": "Acesso restrito a Administradores"},
            )
            return None
        return usuario

    def _servir_estatico(self, caminho: str) -> bool:
        if not DIST_DIR.exists():
            return False
        relativo = caminho.lstrip("/") or "index.html"
        arquivo = (DIST_DIR / relativo).resolve()
        if not str(arquivo).startswith(str(DIST_DIR.resolve())) or not arquivo.is_file():
            arquivo = DIST_DIR / "index.html"
            if not arquivo.is_file():
                return False
        tipo_mime, _ = mimetypes.guess_type(str(arquivo))
        conteudo = arquivo.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", tipo_mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(conteudo)))
        self.end_headers()
        self.wfile.write(conteudo)
        return True

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._enviar_cors()
        self.end_headers()

    def do_GET(self) -> None:
        caminho = urlparse(self.path).path

        if caminho == "/api/health":
            self._enviar_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "clinica": {
                        "nome": config.CLINICA_NOME,
                        "telefone": config.CLINICA_TELEFONE,
                        "duracaoConsultaMinutos": config.CONSULTA_DURACAO_MINUTOS,
                    },
                },
            )
            return

        if caminho == "/api/auth/sessao":
            usuario = self._usuario_autenticado()
            if not usuario:
                self._enviar_json(
                    HTTPStatus.UNAUTHORIZED,
                    {"sucesso": False, "mensagem": "Sessão inválida ou encerrada"},
                )
                return
            self._enviar_json(HTTPStatus.OK, {"usuario": usuario})
            return

        if caminho == "/api/recepcionistas":
            if not self._exigir_administrador():
                return
            try:
                lista = self.recepcionista_controller.listarRecepcionistas()
                self._enviar_json(
                    HTTPStatus.OK,
                    {"recepcionistas": [u.to_dict() for u in lista]},
                )
            except Exception as erro:
                self._enviar_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"sucesso": False, "mensagem": f"Erro ao listar recepcionistas: {erro}"},
                )
            return

        if not caminho.startswith("/api/") and self._servir_estatico(caminho):
            return

        self._enviar_json(HTTPStatus.NOT_FOUND, {"mensagem": "Rota não encontrada"})

    def do_POST(self) -> None:
        caminho = urlparse(self.path).path

        if caminho == "/api/auth/entrar":
            dados = self._ler_json()
            if dados is None:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {"sucesso": False, "mensagem": "JSON inválido"},
                )
                return
            try:
                usuario = self.auth_controller.entrar(
                    str(dados.get("login", "")),
                    str(dados.get("senha", "")),
                )
            except Exception as erro:
                self._enviar_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"sucesso": False, "mensagem": f"Erro ao autenticar no banco de dados: {erro}"},
                )
                return

            if usuario is None:
                self._enviar_json(
                    HTTPStatus.UNAUTHORIZED,
                    {"sucesso": False, "mensagem": "Login ou senha inválidos"},
                )
                return

            token = secrets.token_urlsafe(32)
            usuario_dict = usuario.to_dict()
            SESSOES[token] = usuario_dict
            self._enviar_json(
                HTTPStatus.OK,
                {"sucesso": True, "token": token, "usuario": usuario_dict},
            )
            return

        if caminho == "/api/auth/sair":
            token = self._obter_token()
            if token:
                SESSOES.pop(token, None)
            self._enviar_json(HTTPStatus.OK, {"sucesso": True, "mensagem": "Sessão encerrada"})
            return

        if caminho == "/api/recepcionistas":
            if not self._exigir_administrador():
                return
            dados = self._ler_json()
            if dados is None:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {"sucesso": False, "mensagem": "JSON inválido"},
                )
                return
            try:
                mensagem = self.recepcionista_controller.cadastrarRecepcionista(
                    str(dados.get("nome", "")),
                    str(dados.get("login", "")),
                    str(dados.get("senha", "")),
                )
            except Exception as erro:
                self._enviar_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"sucesso": False, "mensagem": f"Erro ao cadastrar recepcionista: {erro}"},
                )
                return

            if mensagem == "Recepcionista cadastrada com sucesso!":
                self._enviar_json(HTTPStatus.CREATED, {"sucesso": True, "mensagem": mensagem})
            elif mensagem == "Login já utilizado":
                self._enviar_json(HTTPStatus.CONFLICT, {"sucesso": False, "mensagem": mensagem})
            else:
                self._enviar_json(HTTPStatus.BAD_REQUEST, {"sucesso": False, "mensagem": mensagem})
            return

        self._enviar_json(HTTPStatus.NOT_FOUND, {"mensagem": "Rota não encontrada"})

    def do_PUT(self) -> None:
        caminho = urlparse(self.path).path
        match = re.fullmatch(r"/api/recepcionistas/(\d+)", caminho)

        if match:
            if not self._exigir_administrador():
                return
            dados = self._ler_json()
            if dados is None:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {"sucesso": False, "mensagem": "JSON inválido"},
                )
                return

            recepcionista_id = int(match.group(1))
            try:
                mensagem = self.recepcionista_controller.editarRecepcionista(
                    recepcionista_id,
                    str(dados.get("nome", "")),
                    str(dados.get("novaSenha", "")),
                )
            except Exception as erro:
                self._enviar_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"sucesso": False, "mensagem": f"Erro ao editar recepcionista: {erro}"},
                )
                return

            if mensagem == "Recepcionista atualizada com sucesso!":
                self._enviar_json(HTTPStatus.OK, {"sucesso": True, "mensagem": mensagem})
            else:
                self._enviar_json(HTTPStatus.BAD_REQUEST, {"sucesso": False, "mensagem": mensagem})
            return

        self._enviar_json(HTTPStatus.NOT_FOUND, {"mensagem": "Rota não encontrada"})

    def log_message(self, format: str, *args) -> None:
        print(f"[HTTP] {self.address_string()} - {format % args}")


def iniciar_servidor() -> None:
    servidor = ThreadingHTTPServer(
        (config.SERVER_HOST, config.SERVER_PORT),
        AgendaMedicaHandler,
    )
    print(f"Servidor Agenda Médica rodando em http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    iniciar_servidor()
