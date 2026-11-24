"""Testes unitários e de API do Ciclo 3 (UC8, UC9 e RN08 em UC5/UC7) sem dependência do MySQL."""

import sys
import unittest
from datetime import date, datetime, time, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from controller.consulta_controller import ConsultaController
from controller.medico_controller import MedicoController
from controller.paciente_controller import PacienteController
from model.ausencia import Ausencia
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
    grades=None,
) -> Medico:
    med = Medico()
    med.setId(id_med)
    med.setNome(nome)
    med.setCrm("12345")
    med.setUfCrm("RS")
    med.setEspecialidade(_criar_especialidade(1, "Cardiologia"))
    med.setSituacao(situacao)
    med.setGrades(grades or [_criar_grade(DiaSemana.SEGUNDA, time(8, 0), time(10, 0))])
    return med


def _criar_paciente(
    id_pac: int = 5,
    nome: str = "Maria Clara",
    situacao: Situacao = Situacao.ATIVO,
) -> Paciente:
    pac = Paciente()
    pac.setId(id_pac)
    pac.setCpf("12345678901")
    pac.setNome(nome)
    pac.setDataNascimento(date(1992, 5, 10))
    pac.setSexo(Sexo.FEMININO)
    pac.setTelefone("(51) 99999-0000")
    pac.setSituacao(situacao)
    return pac


def _criar_consulta(
    id_cons: int = 100,
    data_hora: datetime = datetime(2026, 12, 7, 9, 0),
    status: StatusConsulta = StatusConsulta.AGENDADA,
) -> Consulta:
    cons = Consulta()
    cons.setId(id_cons)
    cons.setPaciente(_criar_paciente())
    cons.setMedico(_criar_medico())
    cons.setDataHora(data_hora)
    cons.setStatus(status)
    cons.setLembrete(StatusLembrete.PENDENTE)
    return cons


class TestModelosCiclo3(unittest.TestCase):
    def test_grade_gerar_horarios(self) -> None:
        grade = _criar_grade(DiaSemana.SEGUNDA, time(8, 0), time(9, 45))
        self.assertEqual(
            grade.gerarHorarios(30),
            [time(8, 0), time(8, 30), time(9, 0)],
        )
        self.assertEqual(grade.gerarHorarios(0), [])
        self.assertEqual(GradeAtendimento().gerarHorarios(30), [])

    def test_medico_get_grade_do_dia(self) -> None:
        med = _criar_medico(
            grades=[
                _criar_grade(DiaSemana.SEGUNDA, time(8, 0), time(12, 0)),
                _criar_grade(DiaSemana.QUARTA, time(14, 0), time(18, 0)),
            ]
        )
        # 2026-12-07 é segunda-feira; 2026-12-08 é terça; 2026-12-09 é quarta
        grade_seg = med.getGradeDoDia(date(2026, 12, 7))
        self.assertIsNotNone(grade_seg)
        self.assertEqual(grade_seg.getDiaSemana(), DiaSemana.SEGUNDA)
        self.assertIsNone(med.getGradeDoDia(date(2026, 12, 8)))
        grade_qua = med.getGradeDoDia(date(2026, 12, 9))
        self.assertIsNotNone(grade_qua)
        self.assertEqual(grade_qua.getDiaSemana(), DiaSemana.QUARTA)

    def test_consulta_multiplicidade_e_to_dict(self) -> None:
        cons = _criar_consulta()
        self.assertEqual(cons.getStatus(), StatusConsulta.AGENDADA)
        self.assertEqual(cons.getLembrete(), StatusLembrete.PENDENTE)
        self.assertIsNone(cons.getMotivoCancelamento())

        d = cons.to_dict()
        self.assertEqual(d["id"], 100)
        self.assertEqual(d["dataHora"], "2026-12-07T09:00")
        self.assertEqual(d["status"], "AGENDADA")
        self.assertEqual(d["lembrete"], "PENDENTE")
        self.assertEqual(d["medico"]["especialidade"]["nome"], "Cardiologia")

        with self.assertRaises(ValueError):
            cons.setPaciente(None)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            cons.setMedico(None)  # type: ignore[arg-type]


class TestConsultaControllerCU8CU9(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = ConsultaController()
        # Segunda-feira fixa no futuro em relação ao "agora" mockado
        self.agora_fixo = datetime(2026, 12, 7, 8, 15)
        self.data_hoje_seg = date(2026, 12, 7)
        self.data_passada = date(2026, 12, 6)
        self.data_futura_seg = date(2026, 12, 14)

    @patch.object(Paciente, "buscarPorId")
    def test_cu8_verificar_paciente_ativo_inativo_e_nulo(self, mock_buscar: MagicMock) -> None:
        mock_buscar.return_value = None
        self.assertEqual(
            self.controller.verificarPaciente(99),
            "Pacientes inativos não podem ser agendados",
        )

        mock_buscar.return_value = _criar_paciente(situacao=Situacao.INATIVO)
        self.assertEqual(
            self.controller.verificarPaciente(5),
            "Pacientes inativos não podem ser agendados",
        )

        mock_buscar.return_value = _criar_paciente(situacao=Situacao.ATIVO)
        self.assertIsNone(self.controller.verificarPaciente(5))

    @patch.object(Ausencia, "existeAusenciaNaData", return_value=False)
    @patch.object(Consulta, "listarHorariosOcupados")
    @patch.object(Medico, "buscarPorId")
    def test_cu8_listar_horarios_livres_filtra_passados_e_ocupados(
        self,
        mock_buscar_med: MagicMock,
        mock_ocupados: MagicMock,
        _mock_ausencia: MagicMock,
    ) -> None:
        med = _criar_medico(grades=[_criar_grade(DiaSemana.SEGUNDA, time(8, 0), time(10, 0))])
        mock_buscar_med.return_value = med
        mock_ocupados.return_value = [time(9, 0)]

        with patch.object(ConsultaController, "_agora_clinica", return_value=self.agora_fixo):
            # Hoje às 08:15 -> 08:00 já passou, 09:00 ocupado -> restam 08:30 e 09:30
            livres = self.controller.listarHorariosLivres(10, self.data_hoje_seg)
            self.assertEqual(livres, [time(8, 30), time(9, 30)])

            # Data passada -> lista vazia (RN06)
            self.assertEqual(self.controller.listarHorariosLivres(10, self.data_passada), [])

            # Dia sem grade -> lista vazia (RN07)
            self.assertEqual(self.controller.listarHorariosLivres(10, date(2026, 12, 8)), [])

        # Médico inativo -> lista vazia (RN07/RN08)
        mock_buscar_med.return_value = _criar_medico(situacao=Situacao.INATIVO)
        with patch.object(ConsultaController, "_agora_clinica", return_value=self.agora_fixo):
            self.assertEqual(self.controller.listarHorariosLivres(10, self.data_futura_seg), [])

    @patch.object(Ausencia, "existeAusenciaNaData", return_value=False)
    @patch.object(Consulta, "salvar", return_value=True)
    @patch.object(Consulta, "existeConflitoPaciente", return_value=False)
    @patch.object(Consulta, "listarHorariosOcupados", return_value=[])
    @patch.object(Medico, "buscarPorId")
    @patch.object(Paciente, "buscarPorId")
    def test_cu8_agendar_consulta_sucesso_e_bloqueios(
        self,
        mock_pac: MagicMock,
        mock_med: MagicMock,
        mock_ocupados: MagicMock,
        mock_conflito: MagicMock,
        mock_salvar: MagicMock,
        _mock_ausencia: MagicMock,
    ) -> None:
        pac_ativo = _criar_paciente(5, "Maria Clara", Situacao.ATIVO)
        pac_inativo = _criar_paciente(6, "João", Situacao.INATIVO)
        med = _criar_medico(10, "Dr. Carlos", Situacao.ATIVO)
        mock_med.return_value = med

        dt_valida = datetime(2026, 12, 14, 9, 0)

        with patch.object(ConsultaController, "_agora_clinica", return_value=self.agora_fixo):
            # Paciente inativo -> mensagem específica de RN08
            mock_pac.return_value = pac_inativo
            self.assertEqual(
                self.controller.agendarConsulta(6, 10, dt_valida),
                "Pacientes inativos não podem ser agendados",
            )
            mock_conflito.assert_not_called()

            # Horário fora da grade -> Horário indisponível
            mock_pac.return_value = pac_ativo
            self.assertEqual(
                self.controller.agendarConsulta(5, 10, datetime(2026, 12, 14, 15, 0)),
                "Horário indisponível",
            )

            # Conflito de horário do paciente (RN05)
            mock_conflito.return_value = True
            self.assertEqual(
                self.controller.agendarConsulta(5, 10, dt_valida),
                "Paciente já possui consulta agendada neste horário",
            )

            # Sucesso
            mock_conflito.return_value = False
            msg = self.controller.agendarConsulta(5, 10, dt_valida)
            self.assertEqual(
                msg,
                "Consulta agendada com sucesso: 14/12/2026 às 09:00 com Dr. Carlos (Cardiologia)",
            )
            mock_salvar.assert_called_once()

    @patch.object(Consulta, "salvar", return_value=True)
    @patch.object(Consulta, "buscarPorId")
    def test_cu9_cancelar_consulta_fluxos(
        self,
        mock_buscar: MagicMock,
        mock_salvar: MagicMock,
    ) -> None:
        with patch.object(ConsultaController, "_agora_clinica", return_value=self.agora_fixo):
            # Consulta inexistente
            mock_buscar.return_value = None
            self.assertEqual(
                self.controller.cancelarConsulta(999, "Motivo"),
                "Consulta não pode ser cancelada",
            )

            # Consulta já cancelada
            mock_buscar.return_value = _criar_consulta(
                101, datetime(2026, 12, 14, 9, 0), StatusConsulta.CANCELADA
            )
            self.assertEqual(
                self.controller.cancelarConsulta(101, ""),
                "Consulta não pode ser cancelada",
            )

            # Consulta passada (RN03/RN06)
            mock_buscar.return_value = _criar_consulta(
                102, datetime(2026, 12, 7, 8, 0), StatusConsulta.AGENDADA
            )
            self.assertEqual(
                self.controller.cancelarConsulta(102, ""),
                "Consulta não pode ser cancelada",
            )

            # Sucesso sem motivo (opt motivo informado -> permanece None)
            cons_sem_motivo = _criar_consulta(
                103, datetime(2026, 12, 14, 9, 0), StatusConsulta.AGENDADA
            )
            mock_buscar.return_value = cons_sem_motivo
            self.assertEqual(
                self.controller.cancelarConsulta(103, "   "),
                "Consulta cancelada com sucesso!",
            )
            self.assertEqual(cons_sem_motivo.getStatus(), StatusConsulta.CANCELADA)
            self.assertIsNone(cons_sem_motivo.getMotivoCancelamento())

            # Sucesso com motivo
            cons_com_motivo = _criar_consulta(
                104, datetime(2026, 12, 14, 9, 30), StatusConsulta.AGENDADA
            )
            mock_buscar.return_value = cons_com_motivo
            self.assertEqual(
                self.controller.cancelarConsulta(104, "Imprevisto pessoal"),
                "Consulta cancelada com sucesso!",
            )
            self.assertEqual(cons_com_motivo.getStatus(), StatusConsulta.CANCELADA)
            self.assertEqual(cons_com_motivo.getMotivoCancelamento(), "Imprevisto pessoal")
            self.assertEqual(mock_salvar.call_count, 2)


class TestIntegracaoRN08CU5CU7(unittest.TestCase):
    def test_cu5_rn08_bloqueia_alteracao_grade_e_inativacao_mas_permite_editar_nome(self) -> None:
        ctrl = MedicoController()
        grade_atual = [_criar_grade(DiaSemana.SEGUNDA, time(8, 0), time(12, 0))]
        grade_identica_nova_instancia = [_criar_grade(DiaSemana.SEGUNDA, time(8, 0), time(12, 0))]
        grade_alterada = [_criar_grade(DiaSemana.TERCA, time(8, 0), time(12, 0))]
        med = _criar_medico(10, "Dr. Carlos", Situacao.ATIVO, grade_atual)

        with patch.object(Medico, "existeCrmUf", return_value=False), patch.object(
            Medico, "buscarPorId", return_value=med
        ), patch.object(Consulta, "existeFuturaPorMedico", return_value=True) as mock_futura:
            # Editar apenas nome (mesma grade e ATIVO) -> NÃO consulta nem bloqueia
            erro_nome = ctrl.validarMedico(
                10, "Dr. Carlos Silva", "12345", "RS", 1, grade_identica_nova_instancia, Situacao.ATIVO
            )
            self.assertIsNone(erro_nome)
            mock_futura.assert_not_called()

            # Alterar grade com consulta futura -> bloqueia (RN08)
            erro_grade = ctrl.validarMedico(
                10, "Dr. Carlos", "12345", "RS", 1, grade_alterada, Situacao.ATIVO
            )
            self.assertEqual(erro_grade, "Cancele antes as consultas futuras do médico (UC9)")

            # Inativar médico com consulta futura -> bloqueia (RN08)
            erro_inat = ctrl.validarMedico(
                10, "Dr. Carlos", "12345", "RS", 1, grade_identica_nova_instancia, Situacao.INATIVO
            )
            self.assertEqual(erro_inat, "Cancele antes as consultas futuras do médico (UC9)")

    def test_cu7_rn08_bloqueia_inativacao_paciente_com_consulta_futura(self) -> None:
        ctrl = PacienteController()
        consulta_futura = _criar_consulta()

        with patch.object(
            Consulta, "listarFuturasAgendadasPorPaciente", return_value=[consulta_futura]
        ) as mock_futuras:
            # Edição mantendo ATIVO -> não bloqueia
            self.assertIsNone(
                ctrl.validarPaciente(
                    5, "Maria", date(1992, 5, 10), Sexo.FEMININO, "5199999", Situacao.ATIVO
                )
            )
            mock_futuras.assert_not_called()

            # Inativação com consulta futura -> bloqueia (RN08)
            self.assertEqual(
                ctrl.validarPaciente(
                    5, "Maria", date(1992, 5, 10), Sexo.FEMININO, "5199999", Situacao.INATIVO
                ),
                "Cancele antes as consultas futuras do paciente (UC9)",
            )
            mock_futuras.assert_called_once_with(5)


class TestHttpApiCiclo3(unittest.TestCase):
    """Valida as rotas HTTP do Ciclo 3 e controle de acesso por perfil."""

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

    def test_fluxo_api_consultas_cu8_cu9_e_acesso(self) -> None:
        token_admin = self._autenticar(Perfil.ADMINISTRADOR)
        token_rec = self._autenticar(Perfil.RECEPCIONISTA)

        # Administrador não acessa agendamento/cancelamento (403)
        status, _ = self._req("GET", "/api/consultas/medicos-ativos", token=token_admin)
        self.assertEqual(status, 403)

        pac = _criar_paciente(5, "Maria Clara", Situacao.ATIVO)
        med = _criar_medico(10, "Dr. Carlos", Situacao.ATIVO)
        cons = _criar_consulta(100, datetime(2026, 12, 14, 9, 0), StatusConsulta.AGENDADA)
        agora_fixo = datetime(2026, 12, 7, 8, 15)

        with patch.object(Paciente, "buscarPorId", return_value=pac):
            status, dados = self._req("GET", "/api/consultas/pacientes/5/verificar", token=token_rec)
            self.assertEqual(status, 200)
            self.assertTrue(dados["ativo"])

        with patch.object(Medico, "listarAtivos", return_value=[med]):
            status, dados = self._req("GET", "/api/consultas/medicos-ativos", token=token_rec)
            self.assertEqual(status, 200)
            self.assertEqual(len(dados["medicos"]), 1)

        with patch.object(ConsultaController, "_agora_clinica", return_value=agora_fixo), patch.object(
            Medico, "buscarPorId", return_value=med
        ), patch.object(Ausencia, "existeAusenciaNaData", return_value=False), patch.object(
            Consulta, "listarHorariosOcupados", return_value=[time(8, 0)]
        ):
            status, dados = self._req(
                "GET",
                "/api/consultas/horarios-livres?medicoId=10&data=2026-12-14",
                token=token_rec,
            )
            self.assertEqual(status, 200)
            self.assertEqual(dados["horarios"], ["08:30", "09:00", "09:30"])

        with patch.object(ConsultaController, "_agora_clinica", return_value=agora_fixo), patch.object(
            Paciente, "buscarPorId", return_value=pac
        ), patch.object(Medico, "buscarPorId", return_value=med), patch.object(
            Ausencia, "existeAusenciaNaData", return_value=False
        ), patch.object(
            Consulta, "listarHorariosOcupados", return_value=[]
        ), patch.object(Consulta, "existeConflitoPaciente", return_value=False), patch.object(
            Consulta, "salvar", return_value=True
        ):
            status, dados = self._req(
                "POST",
                "/api/consultas",
                {"pacienteId": 5, "medicoId": 10, "dataHora": "2026-12-14T09:00"},
                token=token_rec,
            )
            self.assertEqual(status, 201)
            self.assertIn("Consulta agendada com sucesso", dados["mensagem"])

        with patch.object(Consulta, "listarFuturasAgendadasPorPaciente", return_value=[cons]):
            status, dados = self._req("GET", "/api/consultas/paciente/5/futuras", token=token_rec)
            self.assertEqual(status, 200)
            self.assertEqual(len(dados["consultas"]), 1)

        with patch.object(ConsultaController, "_agora_clinica", return_value=agora_fixo), patch.object(
            Consulta, "buscarPorId", return_value=cons
        ), patch.object(Consulta, "salvar", return_value=True):
            status, dados = self._req(
                "PUT",
                "/api/consultas/100/cancelar",
                {"motivo": "Viagem"},
                token=token_rec,
            )
            self.assertEqual(status, 200)
            self.assertEqual(dados["mensagem"], "Consulta cancelada com sucesso!")


if __name__ == "__main__":
    unittest.main()
