"""Servidor HTTP puro (http.server) da API Agenda Médica — Ciclos 1, 2, 3 e 4."""

from __future__ import annotations

import json
import mimetypes
import re
import secrets
from datetime import date, datetime, time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import config
from controller.ausencia_controller import AusenciaController
from controller.auth_controller import AuthController
from controller.consulta_controller import ConsultaController
from controller.lembrete_controller import LembreteController
from controller.medico_controller import MedicoController
from controller.paciente_controller import PacienteController
from controller.recepcionista_controller import RecepcionistaController
from model.configuracao_clinica import ConfiguracaoClinica
from model.dia_semana import DiaSemana
from model.grade_atendimento import GradeAtendimento
from model.perfil import Perfil
from model.sexo import Sexo
from model.situacao import Situacao

# Sessões ativas em memória: token -> dados públicos do usuário autenticado
SESSOES: Dict[str, dict] = {}

DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"


def _converter_int(valor: object) -> int:
    if isinstance(valor, bool):
        return 0
    try:
        return int(valor)
    except (TypeError, ValueError):
        return 0


def _converter_situacao(valor: object) -> Optional[Situacao]:
    if not isinstance(valor, str):
        return None
    try:
        return Situacao(valor.strip().upper())
    except ValueError:
        return None


def _converter_sexo(valor: object) -> Optional[Sexo]:
    if not isinstance(valor, str):
        return None
    try:
        return Sexo(valor.strip().upper())
    except ValueError:
        return None


def _converter_data(valor: object) -> Optional[date]:
    if not isinstance(valor, str):
        return None
    texto = valor.strip()
    if not texto:
        return None
    try:
        return date.fromisoformat(texto)
    except ValueError:
        return None


def _converter_hora(valor: object) -> Optional[time]:
    if not isinstance(valor, str):
        return None
    texto = valor.strip()
    if not texto:
        return None
    try:
        return time.fromisoformat(texto)
    except ValueError:
        return None


def _converter_data_hora(valor: object) -> Optional[datetime]:
    if not isinstance(valor, str):
        return None
    texto = valor.strip()
    if not texto:
        return None
    try:
        dt = datetime.fromisoformat(texto)
        return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt
    except ValueError:
        return None


def _converter_grades(bruto: object) -> List[GradeAtendimento]:
    if not isinstance(bruto, list):
        return []
    grades: List[GradeAtendimento] = []
    for item in bruto:
        grade = GradeAtendimento()
        if isinstance(item, dict):
            dia_str = item.get("diaSemana")
            if isinstance(dia_str, str):
                try:
                    grade.setDiaSemana(DiaSemana(dia_str.strip().upper()))
                except ValueError:
                    pass
            hora_inicial = _converter_hora(item.get("horaInicial"))
            hora_final = _converter_hora(item.get("horaFinal"))
            if hora_inicial is not None:
                grade.setHoraInicial(hora_inicial)
            if hora_final is not None:
                grade.setHoraFinal(hora_final)
        grades.append(grade)
    return grades


class AgendaMedicaHandler(BaseHTTPRequestHandler):
    auth_controller = AuthController()
    recepcionista_controller = RecepcionistaController()
    medico_controller = MedicoController()
    paciente_controller = PacienteController()
    consulta_controller = ConsultaController()
    lembrete_controller = LembreteController()
    ausencia_controller = AusenciaController()

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

    def _enviar_erro_interno(self, contexto: str, erro: Exception) -> None:
        # O detalhe técnico fica só no console do servidor; o navegador recebe uma mensagem genérica.
        print(f"[ERRO] {contexto}: {erro!r}")
        self._enviar_json(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            {"sucesso": False, "mensagem": f"{contexto}. Tente novamente."},
        )

    def _exigir_perfil(self, perfil_exigido: Perfil, mensagem_negada: str) -> Optional[dict]:
        usuario = self._usuario_autenticado()
        if not usuario:
            self._enviar_json(
                HTTPStatus.UNAUTHORIZED,
                {"sucesso": False, "mensagem": "Usuário não autenticado"},
            )
            return None
        if usuario.get("perfil") != perfil_exigido.value:
            self._enviar_json(
                HTTPStatus.FORBIDDEN,
                {"sucesso": False, "mensagem": mensagem_negada},
            )
            return None
        return usuario

    def _exigir_administrador(self) -> Optional[dict]:
        return self._exigir_perfil(Perfil.ADMINISTRADOR, "Acesso restrito a Administradores")

    def _exigir_recepcionista(self) -> Optional[dict]:
        return self._exigir_perfil(Perfil.RECEPCIONISTA, "Acesso restrito a Recepcionistas")

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
        parsed = urlparse(self.path)
        caminho = parsed.path

        if caminho == "/api/health":
            config_clinica = ConfiguracaoClinica.obter()
            self._enviar_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "clinica": {
                        "nome": config_clinica.getNomeClinica(),
                        "telefone": config_clinica.getTelefoneClinica(),
                        "duracaoConsultaMinutos": config_clinica.getDuracaoConsultaMinutos(),
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
                self._enviar_erro_interno("Erro ao listar recepcionistas", erro)
            return

        if caminho == "/api/especialidades":
            if not self._exigir_administrador():
                return
            try:
                lista = self.medico_controller.listarEspecialidades()
                self._enviar_json(
                    HTTPStatus.OK,
                    {"especialidades": [e.to_dict() for e in lista]},
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao listar especialidades", erro)
            return

        if caminho == "/api/medicos":
            if not self._exigir_administrador():
                return
            try:
                lista = self.medico_controller.listarMedicos()
                self._enviar_json(
                    HTTPStatus.OK,
                    {"medicos": [m.to_dict() for m in lista]},
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao listar médicos", erro)
            return

        match_medico = re.fullmatch(r"/api/medicos/(\d+)", caminho)
        if match_medico:
            if not self._exigir_administrador():
                return
            medico_id = int(match_medico.group(1))
            try:
                medico = self.medico_controller.buscarMedico(medico_id)
            except Exception as erro:
                self._enviar_erro_interno("Erro ao buscar médico", erro)
                return
            if medico is None:
                self._enviar_json(
                    HTTPStatus.NOT_FOUND,
                    {"sucesso": False, "mensagem": "Médico não encontrado"},
                )
                return
            self._enviar_json(HTTPStatus.OK, {"medico": medico.to_dict()})
            return

        if caminho == "/api/pacientes":
            if not self._exigir_recepcionista():
                return
            query = parse_qs(parsed.query)
            termo = query.get("termo", [""])[0]
            try:
                lista = self.paciente_controller.consultarPacientes(termo)
                self._enviar_json(
                    HTTPStatus.OK,
                    {"pacientes": [p.to_dict() for p in lista]},
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao consultar pacientes", erro)
            return

        match_verificar_pac = re.fullmatch(r"/api/consultas/pacientes/(\d+)/verificar", caminho)
        if match_verificar_pac:
            if not self._exigir_recepcionista():
                return
            paciente_id = int(match_verificar_pac.group(1))
            try:
                erro_paciente = self.consulta_controller.verificarPaciente(paciente_id)
            except Exception as erro:
                self._enviar_erro_interno("Erro ao verificar paciente", erro)
                return
            if erro_paciente is None:
                self._enviar_json(HTTPStatus.OK, {"ativo": True, "mensagem": None})
            else:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {"ativo": False, "mensagem": erro_paciente},
                )
            return

        if caminho == "/api/consultas/medicos-ativos":
            if not self._exigir_recepcionista():
                return
            try:
                lista = self.consulta_controller.listarMedicosAtivos()
                self._enviar_json(
                    HTTPStatus.OK,
                    {"medicos": [m.to_dict() for m in lista]},
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao listar médicos ativos", erro)
            return

        if caminho == "/api/consultas/horarios-livres":
            if not self._exigir_recepcionista():
                return
            query = parse_qs(parsed.query)
            medico_id = _converter_int(query.get("medicoId", [""])[0])
            data_consulta = _converter_data(query.get("data", [""])[0])
            try:
                horarios = self.consulta_controller.listarHorariosLivres(medico_id, data_consulta)
                self._enviar_json(
                    HTTPStatus.OK,
                    {"horarios": [h.strftime("%H:%M") for h in horarios]},
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao listar horários livres", erro)
            return

        match_futuras_pac = re.fullmatch(r"/api/consultas/paciente/(\d+)/futuras", caminho)
        if match_futuras_pac:
            if not self._exigir_recepcionista():
                return
            paciente_id = int(match_futuras_pac.group(1))
            try:
                lista = self.consulta_controller.listarConsultasFuturasPaciente(paciente_id)
                self._enviar_json(
                    HTTPStatus.OK,
                    {"consultas": [c.to_dict() for c in lista]},
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao listar consultas do paciente", erro)
            return

        if caminho == "/api/lembretes/pendentes":
            if not self._exigir_recepcionista():
                return
            try:
                lista = self.lembrete_controller.listarLembretesPendentes()
                self._enviar_json(
                    HTTPStatus.OK,
                    {"consultas": [c.to_dict() for c in lista]},
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao listar lembretes pendentes", erro)
            return

        match_link_whatsapp = re.fullmatch(r"/api/lembretes/(\d+)/link-whatsapp", caminho)
        if match_link_whatsapp:
            if not self._exigir_recepcionista():
                return
            consulta_id = int(match_link_whatsapp.group(1))
            try:
                url = self.lembrete_controller.gerarLinkWhatsApp(consulta_id)
            except Exception as erro:
                self._enviar_erro_interno("Erro ao gerar link do WhatsApp", erro)
                return
            if url is None:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "sucesso": False,
                        "url": None,
                        "mensagem": "Consulta não elegível para lembrete",
                    },
                )
            else:
                self._enviar_json(HTTPStatus.OK, {"sucesso": True, "url": url})
            return

        match_ausencias_med = re.fullmatch(r"/api/ausencias/medico/(\d+)/futuras", caminho)
        if match_ausencias_med:
            if not self._exigir_recepcionista():
                return
            medico_id = int(match_ausencias_med.group(1))
            try:
                lista = self.ausencia_controller.listarAusenciasFuturas(medico_id)
                self._enviar_json(
                    HTTPStatus.OK,
                    {"ausencias": [a.to_dict() for a in lista]},
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao listar ausências do médico", erro)
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
                self._enviar_erro_interno("Erro ao autenticar no banco de dados", erro)
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
                self._enviar_erro_interno("Erro ao cadastrar recepcionista", erro)
                return

            if mensagem == "Recepcionista cadastrada com sucesso!":
                self._enviar_json(HTTPStatus.CREATED, {"sucesso": True, "mensagem": mensagem})
            elif mensagem == "Login já utilizado":
                self._enviar_json(HTTPStatus.CONFLICT, {"sucesso": False, "mensagem": mensagem})
            else:
                self._enviar_json(HTTPStatus.BAD_REQUEST, {"sucesso": False, "mensagem": mensagem})
            return

        if caminho == "/api/medicos":
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
                mensagem = self.medico_controller.cadastrarMedico(
                    str(dados.get("nome", "")),
                    str(dados.get("crm", "")),
                    str(dados.get("ufCrm", "")),
                    _converter_int(dados.get("especialidadeId")),
                    _converter_grades(dados.get("grades")),
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao cadastrar médico", erro)
                return

            if mensagem == "Médico cadastrado com sucesso!":
                self._enviar_json(HTTPStatus.CREATED, {"sucesso": True, "mensagem": mensagem})
            elif mensagem == "CRM já cadastrado no sistema":
                self._enviar_json(HTTPStatus.CONFLICT, {"sucesso": False, "mensagem": mensagem})
            else:
                self._enviar_json(HTTPStatus.BAD_REQUEST, {"sucesso": False, "mensagem": mensagem})
            return

        match_validar_medico = re.fullmatch(r"/api/medicos/(\d+)/validar", caminho)
        if match_validar_medico:
            if not self._exigir_administrador():
                return
            dados = self._ler_json()
            if dados is None:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {"sucesso": False, "mensagem": "JSON inválido"},
                )
                return
            medico_id = int(match_validar_medico.group(1))
            try:
                erro_validacao = self.medico_controller.validarMedico(
                    medico_id,
                    str(dados.get("nome", "")),
                    str(dados.get("crm", "")),
                    str(dados.get("ufCrm", "")),
                    _converter_int(dados.get("especialidadeId")),
                    _converter_grades(dados.get("grades")),
                    _converter_situacao(dados.get("situacao")),
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao validar médico", erro)
                return

            if erro_validacao is None:
                self._enviar_json(HTTPStatus.OK, {"valido": True, "mensagem": None})
            elif erro_validacao == "CRM já cadastrado no sistema" or erro_validacao.startswith("Cancele antes"):
                self._enviar_json(
                    HTTPStatus.CONFLICT,
                    {"valido": False, "mensagem": erro_validacao},
                )
            else:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {"valido": False, "mensagem": erro_validacao},
                )
            return

        if caminho == "/api/pacientes":
            if not self._exigir_recepcionista():
                return
            dados = self._ler_json()
            if dados is None:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {"sucesso": False, "mensagem": "JSON inválido"},
                )
                return
            try:
                mensagem = self.paciente_controller.cadastrarPaciente(
                    str(dados.get("cpf", "")),
                    str(dados.get("nome", "")),
                    _converter_data(dados.get("dataNascimento")),
                    _converter_sexo(dados.get("sexo")),
                    str(dados.get("telefone", "")),
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao cadastrar paciente", erro)
                return

            if mensagem == "Paciente cadastrado com sucesso!":
                self._enviar_json(HTTPStatus.CREATED, {"sucesso": True, "mensagem": mensagem})
            elif mensagem.startswith("CPF já cadastrado no sistema"):
                self._enviar_json(HTTPStatus.CONFLICT, {"sucesso": False, "mensagem": mensagem})
            else:
                self._enviar_json(HTTPStatus.BAD_REQUEST, {"sucesso": False, "mensagem": mensagem})
            return

        match_validar_paciente = re.fullmatch(r"/api/pacientes/(\d+)/validar", caminho)
        if match_validar_paciente:
            if not self._exigir_recepcionista():
                return
            dados = self._ler_json()
            if dados is None:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {"sucesso": False, "mensagem": "JSON inválido"},
                )
                return
            paciente_id = int(match_validar_paciente.group(1))
            try:
                erro_validacao = self.paciente_controller.validarPaciente(
                    paciente_id,
                    str(dados.get("nome", "")),
                    _converter_data(dados.get("dataNascimento")),
                    _converter_sexo(dados.get("sexo")),
                    str(dados.get("telefone", "")),
                    _converter_situacao(dados.get("situacao")),
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao validar paciente", erro)
                return

            if erro_validacao is None:
                self._enviar_json(HTTPStatus.OK, {"valido": True, "mensagem": None})
            elif erro_validacao.startswith("Cancele antes"):
                self._enviar_json(
                    HTTPStatus.CONFLICT,
                    {"valido": False, "mensagem": erro_validacao},
                )
            else:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {"valido": False, "mensagem": erro_validacao},
                )
            return

        if caminho == "/api/consultas":
            if not self._exigir_recepcionista():
                return
            dados = self._ler_json()
            if dados is None:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {"sucesso": False, "mensagem": "JSON inválido"},
                )
                return
            try:
                mensagem = self.consulta_controller.agendarConsulta(
                    _converter_int(dados.get("pacienteId")),
                    _converter_int(dados.get("medicoId")),
                    _converter_data_hora(dados.get("dataHora")),
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao agendar consulta", erro)
                return

            if mensagem.startswith("Consulta agendada com sucesso"):
                self._enviar_json(HTTPStatus.CREATED, {"sucesso": True, "mensagem": mensagem})
            elif mensagem in (
                "Horário indisponível",
                "Paciente já possui consulta agendada neste horário",
            ):
                self._enviar_json(HTTPStatus.CONFLICT, {"sucesso": False, "mensagem": mensagem})
            else:
                self._enviar_json(HTTPStatus.BAD_REQUEST, {"sucesso": False, "mensagem": mensagem})
            return

        if caminho == "/api/ausencias/validar":
            if not self._exigir_recepcionista():
                return
            dados = self._ler_json()
            if dados is None:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {"sucesso": False, "mensagem": "JSON inválido"},
                )
                return
            try:
                erro_validacao = self.ausencia_controller.validarAusencia(
                    _converter_int(dados.get("medicoId")),
                    str(dados.get("motivo", "")),
                    _converter_data(dados.get("dataInicial")),
                    _converter_data(dados.get("dataFinal")),
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao validar ausência", erro)
                return

            if erro_validacao is None:
                self._enviar_json(HTTPStatus.OK, {"valido": True, "mensagem": None})
            elif erro_validacao.startswith("Existem consultas"):
                self._enviar_json(
                    HTTPStatus.CONFLICT,
                    {"valido": False, "mensagem": erro_validacao},
                )
            else:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {"valido": False, "mensagem": erro_validacao},
                )
            return

        if caminho == "/api/ausencias":
            if not self._exigir_recepcionista():
                return
            dados = self._ler_json()
            if dados is None:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {"sucesso": False, "mensagem": "JSON inválido"},
                )
                return
            try:
                mensagem = self.ausencia_controller.registrarAusencia(
                    _converter_int(dados.get("medicoId")),
                    str(dados.get("motivo", "")),
                    _converter_data(dados.get("dataInicial")),
                    _converter_data(dados.get("dataFinal")),
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao registrar ausência", erro)
                return

            if mensagem == "Ausência registrada com sucesso!":
                self._enviar_json(HTTPStatus.CREATED, {"sucesso": True, "mensagem": mensagem})
            elif mensagem.startswith("Existem consultas"):
                self._enviar_json(HTTPStatus.CONFLICT, {"sucesso": False, "mensagem": mensagem})
            else:
                self._enviar_json(HTTPStatus.BAD_REQUEST, {"sucesso": False, "mensagem": mensagem})
            return

        self._enviar_json(HTTPStatus.NOT_FOUND, {"mensagem": "Rota não encontrada"})

    def do_PUT(self) -> None:
        caminho = urlparse(self.path).path

        match_rec = re.fullmatch(r"/api/recepcionistas/(\d+)", caminho)
        if match_rec:
            if not self._exigir_administrador():
                return
            dados = self._ler_json()
            if dados is None:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {"sucesso": False, "mensagem": "JSON inválido"},
                )
                return

            recepcionista_id = int(match_rec.group(1))
            try:
                mensagem = self.recepcionista_controller.editarRecepcionista(
                    recepcionista_id,
                    str(dados.get("nome", "")),
                    str(dados.get("novaSenha", "")),
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao editar recepcionista", erro)
                return

            if mensagem == "Recepcionista atualizada com sucesso!":
                self._enviar_json(HTTPStatus.OK, {"sucesso": True, "mensagem": mensagem})
            else:
                self._enviar_json(HTTPStatus.BAD_REQUEST, {"sucesso": False, "mensagem": mensagem})
            return

        match_med = re.fullmatch(r"/api/medicos/(\d+)", caminho)
        if match_med:
            if not self._exigir_administrador():
                return
            dados = self._ler_json()
            if dados is None:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {"sucesso": False, "mensagem": "JSON inválido"},
                )
                return

            medico_id = int(match_med.group(1))
            try:
                mensagem = self.medico_controller.editarMedico(
                    medico_id,
                    str(dados.get("nome", "")),
                    str(dados.get("crm", "")),
                    str(dados.get("ufCrm", "")),
                    _converter_int(dados.get("especialidadeId")),
                    _converter_grades(dados.get("grades")),
                    _converter_situacao(dados.get("situacao")),
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao editar médico", erro)
                return

            if mensagem == "Médico atualizado com sucesso!":
                self._enviar_json(HTTPStatus.OK, {"sucesso": True, "mensagem": mensagem})
            elif mensagem == "CRM já cadastrado no sistema" or mensagem.startswith("Cancele antes"):
                self._enviar_json(HTTPStatus.CONFLICT, {"sucesso": False, "mensagem": mensagem})
            else:
                self._enviar_json(HTTPStatus.BAD_REQUEST, {"sucesso": False, "mensagem": mensagem})
            return

        match_pac = re.fullmatch(r"/api/pacientes/(\d+)", caminho)
        if match_pac:
            if not self._exigir_recepcionista():
                return
            dados = self._ler_json()
            if dados is None:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {"sucesso": False, "mensagem": "JSON inválido"},
                )
                return

            paciente_id = int(match_pac.group(1))
            try:
                mensagem = self.paciente_controller.editarPaciente(
                    paciente_id,
                    str(dados.get("nome", "")),
                    _converter_data(dados.get("dataNascimento")),
                    _converter_sexo(dados.get("sexo")),
                    str(dados.get("telefone", "")),
                    _converter_situacao(dados.get("situacao")),
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao editar paciente", erro)
                return

            if mensagem == "Dados do paciente atualizados com sucesso!":
                self._enviar_json(HTTPStatus.OK, {"sucesso": True, "mensagem": mensagem})
            elif mensagem.startswith("Cancele antes"):
                self._enviar_json(HTTPStatus.CONFLICT, {"sucesso": False, "mensagem": mensagem})
            else:
                self._enviar_json(HTTPStatus.BAD_REQUEST, {"sucesso": False, "mensagem": mensagem})
            return

        match_cancelar_consulta = re.fullmatch(r"/api/consultas/(\d+)/cancelar", caminho)
        if match_cancelar_consulta:
            if not self._exigir_recepcionista():
                return
            dados = self._ler_json()
            if dados is None:
                self._enviar_json(
                    HTTPStatus.BAD_REQUEST,
                    {"sucesso": False, "mensagem": "JSON inválido"},
                )
                return

            consulta_id = int(match_cancelar_consulta.group(1))
            try:
                mensagem = self.consulta_controller.cancelarConsulta(
                    consulta_id,
                    str(dados.get("motivo", "")),
                )
            except Exception as erro:
                self._enviar_erro_interno("Erro ao cancelar consulta", erro)
                return

            if mensagem == "Consulta cancelada com sucesso!":
                self._enviar_json(HTTPStatus.OK, {"sucesso": True, "mensagem": mensagem})
            else:
                self._enviar_json(HTTPStatus.BAD_REQUEST, {"sucesso": False, "mensagem": mensagem})
            return

        match_confirmar_lembrete = re.fullmatch(r"/api/lembretes/(\d+)/confirmar", caminho)
        if match_confirmar_lembrete:
            if not self._exigir_recepcionista():
                return
            consulta_id = int(match_confirmar_lembrete.group(1))
            try:
                mensagem = self.lembrete_controller.confirmarEnvio(consulta_id)
            except Exception as erro:
                self._enviar_erro_interno("Erro ao confirmar envio do lembrete", erro)
                return

            if mensagem == "Lembrete marcado como enviado!":
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
