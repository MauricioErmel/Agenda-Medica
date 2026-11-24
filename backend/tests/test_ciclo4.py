"""Testes unitários e de API do Ciclo 4 (UC10, UC11 e integração RN07/RN10/RNF04 no UC8)."""

import sys
import unittest
from datetime import date, datetime, time
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import unquote

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from controller.ausencia_controller import AusenciaController
from controller.consulta_controller import ConsultaController
from controller.lembrete_controller import LembreteController
from model.ausencia import Ausencia
from model.configuracao_clinica import ConfiguracaoClinica
from model.consulta import Consulta
from model.dia_semana import DiaSemana
from model.especialidade import Especialidade
from model.grade_atendimento import GradeAtendimento
from model.medico import Medico
from model.paciente import Paciente
from model.perfil import Perfil
from model.sexo import Sexo
from model.situacao import Situacao
from model.status_consulta import StatusConsulta
from model.status_lembrete import StatusLembrete
from model.usuario import Usuario


def _criar_grade(dia: DiaSemana, inicio: time, fim: time) -> GradeAtendimento:
    grade = GradeAtendimento()
    grade.setDiaSemana(dia)
    grade.setHoraInicial(inicio)
    grade.setHoraFinal(fim)
    return grade


def _criar_especialidade(id_esp: int = 1, nome: str = "Cardiologia") -> Especialidade:
    esp = Especialidade()
    esp.setId(id_esp)
    esp.setNome(nome)
    return esp


def _criar_medico(
    id_med: int = 10,
    nome: str = "Dr. Carlos",
    situacao: Situacao = Situacao.ATIVO,
) -> Medico:
    med = Medico()
    med.setId(id_med)
    med.setNome(nome)
    med.setCrm("12345")
    med.setUfCrm("RS")
    med.setEspecialidade(_criar_especialidade(1, "Cardiologia"))
    med.setSituacao(situacao)
    med.setGrades([_criar_grade(DiaSemana.SEGUNDA, time(8, 0), time(10, 0))])
    return med


def _criar_paciente(
    id_pac: int = 5,
    nome: str = "Maria Clara",
    telefone: str = "(51) 99999-0000",
    situacao: Situacao = Situacao.ATIVO,
) -> Paciente:
    pac = Paciente()
    pac.setId(id_pac)
    pac.setCpf("12345678901")
    pac.setNome(nome)
    pac.setDataNascimento(date(1992, 5, 10))
    pac.setSexo(Sexo.FEMININO)
    pac.setTelefone(telefone)
    pac.setSituacao(situacao)
    return pac


def _criar_consulta(
    id_cons: int = 100,
    data_hora: datetime = datetime(2026, 12, 14, 9, 0),
    status: StatusConsulta = StatusConsulta.AGENDADA,
    lembrete: StatusLembrete = StatusLembrete.PENDENTE,
) -> Consulta:
    cons = Consulta()
    cons.setId(id_cons)
    cons.setPaciente(_criar_paciente())
    cons.setMedico(_criar_medico())
    cons.setDataHora(data_hora)
    cons.setStatus(status)
    cons.setLembrete(lembrete)
    return cons


def _criar_ausencia(
    id_aus: int = 1,
    motivo: str = "Congresso médico",
    data_inicial: date = date(2026, 12, 14),
    data_final: date = date(2026, 12, 16),
) -> Ausencia:
    aus = Ausencia()
    aus.setId(id_aus)
    aus.setMedico(_criar_medico())
    aus.setMotivo(motivo)
    aus.setDataInicial(data_inicial)
    aus.setDataFinal(data_final)
    return aus


class TestModelosCiclo4(unittest.TestCase):
    def test_configuracao_clinica_obter_e_to_dict(self) -> None:
        cfg = ConfiguracaoClinica.obter()
        self.assertTrue(bool(cfg.getNomeClinica()))
        self.assertTrue(bool(cfg.getTelefoneClinica()))
        self.assertGreater(cfg.getDuracaoConsultaMinutos(), 0)
        d = cfg.to_dict()
        self.assertEqual(d["nomeClinica"], cfg.getNomeClinica())
        self.assertEqual(d["telefoneClinica"], cfg.getTelefoneClinica())
        self.assertEqual(d["duracaoConsultaMinutos"], cfg.getDuracaoConsultaMinutos())

    def test_ausencia_multiplicidade_e_to_dict(self) -> None:
        aus = _criar_ausencia()
        self.assertEqual(aus.getId(), 1)
        self.assertEqual(aus.getMotivo(), "Congresso médico")
        self.assertEqual(aus.getDataInicial(), date(2026, 12, 14))
        self.assertEqual(aus.getDataFinal(), date(2026, 12, 16))
        d = aus.to_dict()
        self.assertEqual(d["dataInicial"], "2026-12-14")
        self.assertEqual(d["dataFinal"], "2026-12-16")
        self.assertEqual(d["medico"]["nome"], "Dr. Carlos")

        with self.assertRaises(ValueError):
            aus.setMedico(None)  # type: ignore[arg-type]

    def test_consulta_is_lembrete_pendente(self) -> None:
        agora_fixo = datetime(2026, 12, 7, 8, 15)
        with patch.object(Consulta, "_agora_clinica", return_value=agora_fixo):
            cons_elegivel = _criar_consulta(1, datetime(2026, 12, 14, 9, 0))
            self.assertTrue(cons_elegivel.isLembretePendente())

            cons_passada = _criar_consulta(2, datetime(2026, 12, 7, 8, 0))
            self.assertFalse(cons_passada.isLembretePendente())

            cons_cancelada = _criar_consulta(
                3, datetime(2026, 12, 14, 9, 0), StatusConsulta.CANCELADA
            )
            self.assertFalse(cons_cancelada.isLembretePendente())

            cons_enviada = _criar_consulta(
                4,
                datetime(2026, 12, 14, 9, 0),
                StatusConsulta.AGENDADA,
                StatusLembrete.ENVIADO,
            )
            self.assertFalse(cons_enviada.isLembretePendente())


class TestLembreteControllerCU10(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = LembreteController()
        self.agora_fixo = datetime(2026, 12, 7, 8, 15)

    @patch.object(Consulta, "listarLembretesPendentes")
    def test_cu10_listar_lembretes_pendentes(self, mock_listar: MagicMock) -> None:
        cons = _criar_consulta()
        mock_listar.return_value = [cons]
        resultado = self.controller.listarLembretesPendentes()
        self.assertEqual(resultado, [cons])
        mock_listar.assert_called_once()

    @patch.object(Consulta, "buscarPorId")
    def test_cu10_gerar_link_whatsapp_elegivel_e_inelegivel(
        self,
        mock_buscar: MagicMock,
    ) -> None:
        with patch.object(Consulta, "_agora_clinica", return_value=self.agora_fixo):
            mock_buscar.return_value = None
            self.assertIsNone(self.controller.gerarLinkWhatsApp(999))

            cons_enviada = _criar_consulta(lembrete=StatusLembrete.ENVIADO)
            mock_buscar.return_value = cons_enviada
            self.assertIsNone(self.controller.gerarLinkWhatsApp(100))

            cons_ok = _criar_consulta(100, datetime(2026, 12, 14, 9, 0))
            mock_buscar.return_value = cons_ok
            url = self.controller.gerarLinkWhatsApp(100)
            self.assertIsNotNone(url)
            self.assertTrue(url.startswith("https://wa.me/5551999990000?text="))
            texto = unquote(url.split("?text=", 1)[1])
            cfg = ConfiguracaoClinica.obter()
            self.assertIn("Maria Clara", texto)
            self.assertIn(cfg.getNomeClinica(), texto)
            self.assertIn("Dr. Carlos", texto)
            self.assertIn("14/12/2026 às 09:00", texto)
            self.assertIn(cfg.getTelefoneClinica(), texto)

    @patch.object(Consulta, "salvar", return_value=True)
    @patch.object(Consulta, "buscarPorId")
    def test_cu10_confirmar_envio(
        self,
        mock_buscar: MagicMock,
        mock_salvar: MagicMock,
    ) -> None:
        with patch.object(Consulta, "_agora_clinica", return_value=self.agora_fixo):
            mock_buscar.return_value = None
            self.assertEqual(
                self.controller.confirmarEnvio(999),
                "Consulta não elegível para lembrete",
            )

            cons = _criar_consulta(100, datetime(2026, 12, 14, 9, 0))
            mock_buscar.return_value = cons
            msg = self.controller.confirmarEnvio(100)
            self.assertEqual(msg, "Lembrete marcado como enviado!")
            self.assertEqual(cons.getLembrete(), StatusLembrete.ENVIADO)
            mock_salvar.assert_called_once()


class TestAusenciaControllerCU11(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = AusenciaController()
        self.agora_fixo = datetime(2026, 12, 7, 8, 15)

    @patch.object(Consulta, "existeFuturaPorMedicoNoPeriodo", return_value=False)
    @patch.object(Medico, "buscarPorId")
    def test_cu11_validar_ausencia_regras(
        self,
        mock_med: MagicMock,
        mock_existe_cons: MagicMock,
    ) -> None:
        med_ativo = _criar_medico(10, "Dr. Carlos", Situacao.ATIVO)
        med_inativo = _criar_medico(11, "Dr. Inativo", Situacao.INATIVO)

        with patch.object(AusenciaController, "_agora_clinica", return_value=self.agora_fixo):
            # Médico inexistente
            mock_med.return_value = None
            self.assertEqual(
                self.controller.validarAusencia(99, "Férias", date(2026, 12, 14), date(2026, 12, 15)),
                "Dados inválidos para registro de ausência",
            )

            # Médico inativo
            mock_med.return_value = med_inativo
            self.assertEqual(
                self.controller.validarAusencia(11, "Férias", date(2026, 12, 14), date(2026, 12, 15)),
                "Dados inválidos para registro de ausência",
            )

            # Motivo vazio
            mock_med.return_value = med_ativo
            self.assertEqual(
                self.controller.validarAusencia(10, "   ", date(2026, 12, 14), date(2026, 12, 15)),
                "Dados inválidos para registro de ausência",
            )

            # Data passada (RN06)
            self.assertEqual(
                self.controller.validarAusencia(10, "Férias", date(2026, 12, 6), date(2026, 12, 10)),
                "Dados inválidos para registro de ausência",
            )

            # Data final anterior à inicial (RN10)
            self.assertEqual(
                self.controller.validarAusencia(10, "Férias", date(2026, 12, 15), date(2026, 12, 14)),
                "Dados inválidos para registro de ausência",
            )

            # Existe consulta futura no período (RN10)
            mock_existe_cons.return_value = True
            self.assertEqual(
                self.controller.validarAusencia(10, "Férias", date(2026, 12, 14), date(2026, 12, 15)),
                "Existem consultas futuras agendadas no período; cancele-as antes (UC9)",
            )

            # Válido (mesmo dia: dataInicial == dataFinal)
            mock_existe_cons.return_value = False
            self.assertIsNone(
                self.controller.validarAusencia(10, "Congresso", date(2026, 12, 7), date(2026, 12, 7))
            )

    @patch.object(Ausencia, "salvar", return_value=True)
    @patch.object(Consulta, "existeFuturaPorMedicoNoPeriodo", return_value=False)
    @patch.object(Medico, "buscarPorId")
    def test_cu11_registrar_ausencia_sucesso(
        self,
        mock_med: MagicMock,
        _mock_existe: MagicMock,
        mock_salvar: MagicMock,
    ) -> None:
        mock_med.return_value = _criar_medico(10, "Dr. Carlos", Situacao.ATIVO)
        with patch.object(AusenciaController, "_agora_clinica", return_value=self.agora_fixo):
            msg = self.controller.registrarAusencia(
                10, "Congresso médico", date(2026, 12, 14), date(2026, 12, 16)
            )
            self.assertEqual(msg, "Ausência registrada com sucesso!")
            mock_salvar.assert_called_once()


class TestIntegracaoCU8AusenciaEConfiguracao(unittest.TestCase):
    def test_cu8_bloqueia_horarios_quando_ha_ausencia_e_usa_configuracao(self) -> None:
        ctrl = ConsultaController()
        agora_fixo = datetime(2026, 12, 7, 8, 15)
        med = _criar_medico(10, "Dr. Carlos", Situacao.ATIVO)
        pac = _criar_paciente(5, "Maria Clara", situacao=Situacao.ATIVO)

        with patch.object(ConsultaController, "_agora_clinica", return_value=agora_fixo), patch.object(
            Medico, "buscarPorId", return_value=med
        ), patch.object(Paciente, "buscarPorId", return_value=pac), patch.object(
            Ausencia, "existeAusenciaNaData", return_value=True
        ) as mock_ausencia, patch.object(
            Consulta, "listarHorariosOcupados", return_value=[]
        ) as mock_ocupados:
            self.assertEqual(ctrl.listarHorariosLivres(10, date(2026, 12, 14)), [])
            mock_ausencia.assert_called_with(10, date(2026, 12, 14))
            mock_ocupados.assert_not_called()

            # Agendamento na data bloqueada também é recusado
            self.assertEqual(
                ctrl.agendarConsulta(5, 10, datetime(2026, 12, 14, 9, 0)),
                "Horário indisponível",
            )


class TestHttpApiCiclo4(unittest.TestCase):
    """Valida as rotas HTTP do Ciclo 4 (UC10 e UC11) e controle de acesso por perfil."""

    @classmethod
    def setUpClass(cls) -> None:
        import threading
        from http.server import ThreadingHTTPServer
        import server

        cls.server_module = server
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.AgendaMedicaHandler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def setUp(self) -> None:
        self.server_module.SESSOES.clear()

    def _req(self, metodo: str, caminho: str, corpo=None, token=None):
        import json
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen

        url = f"http://127.0.0.1:{self.port}{caminho}"
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        data = json.dumps(corpo).encode("utf-8") if corpo is not None else None
        req = Request(url, data=data, headers=headers, method=metodo)
        try:
            with urlopen(req) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except HTTPError as err:
            return err.code, json.loads(err.read().decode("utf-8"))

    def _autenticar(self, perfil: Perfil) -> str:
        usuario = Usuario()
        usuario.setId(1 if perfil == Perfil.ADMINISTRADOR else 2)
        usuario.setNome("Admin" if perfil == Perfil.ADMINISTRADOR else "Rec")
        usuario.setLogin("admin" if perfil == Perfil.ADMINISTRADOR else "rec")
        usuario.setPerfil(perfil)
        with patch.object(Usuario, "autenticar", return_value=usuario):
            status, dados = self._req(
                "POST", "/api/auth/entrar", {"login": usuario.getLogin(), "senha": "123"}
            )
            self.assertEqual(status, 200)
            return dados["token"]

    def test_fluxo_api_cu10_cu11_e_acesso(self) -> None:
        token_admin = self._autenticar(Perfil.ADMINISTRADOR)
        token_rec = self._autenticar(Perfil.RECEPCIONISTA)

        # Administrador não acessa lembretes nem ausências (403)
        status, _ = self._req("GET", "/api/lembretes/pendentes", token=token_admin)
        self.assertEqual(status, 403)
        status, _ = self._req("GET", "/api/ausencias/medico/10/futuras", token=token_admin)
        self.assertEqual(status, 403)

        agora_fixo = datetime(2026, 12, 7, 8, 15)
        cons = _criar_consulta(100, datetime(2026, 12, 14, 9, 0))
        med = _criar_medico(10, "Dr. Carlos", Situacao.ATIVO)
        aus = _criar_ausencia(1, "Congresso", date(2026, 12, 14), date(2026, 12, 16))

        # UC10: listar pendentes, gerar link WhatsApp e confirmar envio
        with patch.object(Consulta, "listarLembretesPendentes", return_value=[cons]):
            status, dados = self._req("GET", "/api/lembretes/pendentes", token=token_rec)
            self.assertEqual(status, 200)
            self.assertEqual(len(dados["consultas"]), 1)

        with patch.object(Consulta, "_agora_clinica", return_value=agora_fixo), patch.object(
            Consulta, "buscarPorId", return_value=cons
        ):
            status, dados = self._req("GET", "/api/lembretes/100/link-whatsapp", token=token_rec)
            self.assertEqual(status, 200)
            self.assertTrue(dados["url"].startswith("https://wa.me/"))

        with patch.object(Consulta, "_agora_clinica", return_value=agora_fixo), patch.object(
            Consulta, "buscarPorId", return_value=cons
        ), patch.object(Consulta, "salvar", return_value=True):
            status, dados = self._req("PUT", "/api/lembretes/100/confirmar", token=token_rec)
            self.assertEqual(status, 200)
            self.assertEqual(dados["mensagem"], "Lembrete marcado como enviado!")

        # UC11: listar ausências futuras, validar (conflito e sucesso) e registrar
        with patch.object(Ausencia, "listarFuturasPorMedico", return_value=[aus]):
            status, dados = self._req("GET", "/api/ausencias/medico/10/futuras", token=token_rec)
            self.assertEqual(status, 200)
            self.assertEqual(len(dados["ausencias"]), 1)

        with patch.object(AusenciaController, "_agora_clinica", return_value=agora_fixo), patch.object(
            Medico, "buscarPorId", return_value=med
        ), patch.object(Consulta, "existeFuturaPorMedicoNoPeriodo", return_value=True):
            status, dados = self._req(
                "POST",
                "/api/ausencias/validar",
                {
                    "medicoId": 10,
                    "motivo": "Congresso",
                    "dataInicial": "2026-12-14",
                    "dataFinal": "2026-12-16",
                },
                token=token_rec,
            )
            self.assertEqual(status, 409)
            self.assertFalse(dados["valido"])

        with patch.object(AusenciaController, "_agora_clinica", return_value=agora_fixo), patch.object(
            Medico, "buscarPorId", return_value=med
        ), patch.object(Consulta, "existeFuturaPorMedicoNoPeriodo", return_value=False), patch.object(
            Ausencia, "salvar", return_value=True
        ):
            status, dados = self._req(
                "POST",
                "/api/ausencias/validar",
                {
                    "medicoId": 10,
                    "motivo": "Congresso",
                    "dataInicial": "2026-12-14",
                    "dataFinal": "2026-12-16",
                },
                token=token_rec,
            )
            self.assertEqual(status, 200)
            self.assertTrue(dados["valido"])

            status, dados = self._req(
                "POST",
                "/api/ausencias",
                {
                    "medicoId": 10,
                    "motivo": "Congresso",
                    "dataInicial": "2026-12-14",
                    "dataFinal": "2026-12-16",
                },
                token=token_rec,
            )
            self.assertEqual(status, 201)
            self.assertEqual(dados["mensagem"], "Ausência registrada com sucesso!")


if __name__ == "__main__":
    unittest.main()
