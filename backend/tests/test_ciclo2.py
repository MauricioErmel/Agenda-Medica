"""Testes unitários e de API do Ciclo 2 (CU4, CU5, CU6, CU7) sem dependência do MySQL."""

import sys
import unittest
from datetime import date, time, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from controller.medico_controller import MedicoController
from controller.paciente_controller import PacienteController
from model.dia_semana import DiaSemana
from model.especialidade import Especialidade
from model.grade_atendimento import GradeAtendimento
from model.medico import Medico
from model.paciente import Paciente
from model.perfil import Perfil
from model.sexo import Sexo
from model.situacao import Situacao
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


class TestModelosCiclo2(unittest.TestCase):
    def test_grade_atendimento_horario_valido_e_conversao_timedelta(self) -> None:
        g_valida = _criar_grade(DiaSemana.SEGUNDA, time(8, 0), time(12, 0))
        self.assertTrue(g_valida.isHorarioValido())
        self.assertEqual(
            g_valida.to_dict(),
            {
                "id": None,
                "diaSemana": "SEGUNDA",
                "horaInicial": "08:00",
                "horaFinal": "12:00",
            },
        )

        g_igual = _criar_grade(DiaSemana.SEGUNDA, time(8, 0), time(8, 0))
        self.assertFalse(g_igual.isHorarioValido())

        g_invertida = _criar_grade(DiaSemana.TERCA, time(14, 0), time(10, 0))
        self.assertFalse(g_invertida.isHorarioValido())

        g_vazia = GradeAtendimento()
        self.assertFalse(g_vazia.isHorarioValido())

        montada = GradeAtendimento._montar_grade(
            {
                "id": 5,
                "dia_semana": "QUARTA",
                "hora_inicial": timedelta(hours=9, minutes=30),
                "hora_final": timedelta(hours=17, minutes=0),
            }
        )
        self.assertEqual(montada.getId(), 5)
        self.assertEqual(montada.getDiaSemana(), DiaSemana.QUARTA)
        self.assertEqual(montada.getHoraInicial(), time(9, 30))
        self.assertEqual(montada.getHoraFinal(), time(17, 0))
        self.assertTrue(montada.isHorarioValido())

    def test_medico_composicao_grades_e_multiplicidades(self) -> None:
        medico = Medico()
        esp = _criar_especialidade(2, "Pediatria")
        medico.setEspecialidade(esp)
        self.assertIs(medico.getEspecialidade(), esp)

        with self.assertRaises(ValueError):
            medico.setEspecialidade(None)  # type: ignore[arg-type]

        with self.assertRaises(ValueError):
            medico.setGrades([])

        g_sex = _criar_grade(DiaSemana.SEXTA, time(13, 0), time(18, 0))
        g_seg = _criar_grade(DiaSemana.SEGUNDA, time(8, 0), time(12, 0))
        medico.setGrades([g_sex, g_seg])

        # Ordenado por dia da semana e isolado por composição (alterar objeto externo não afeta)
        g_seg.setHoraFinal(time(10, 0))
        grades = medico.getGrades()
        self.assertEqual([g.getDiaSemana() for g in grades], [DiaSemana.SEGUNDA, DiaSemana.SEXTA])
        self.assertEqual(grades[0].getHoraFinal(), time(12, 0))

        # Não permite dias duplicados
        with self.assertRaises(ValueError):
            medico.setGrades(
                [
                    _criar_grade(DiaSemana.SEGUNDA, time(8, 0), time(12, 0)),
                    _criar_grade(DiaSemana.SEGUNDA, time(14, 0), time(18, 0)),
                ]
            )

    def test_paciente_normalizacao_cpf_e_to_dict(self) -> None:
        pac = Paciente()
        pac.setId(7)
        pac.setCpf("123.456.789-01")
        pac.setNome("João Pereira")
        pac.setDataNascimento(date(1990, 5, 15))
        pac.setSexo(Sexo.MASCULINO)
        pac.setTelefone("(51) 99999-1111")
        pac.setSituacao(Situacao.ATIVO)

        self.assertEqual(pac.getCpf(), "12345678901")
        self.assertEqual(
            pac.to_dict(),
            {
                "id": 7,
                "cpf": "12345678901",
                "nome": "João Pereira",
                "dataNascimento": "1990-05-15",
                "sexo": "MASCULINO",
                "telefone": "(51) 99999-1111",
                "situacao": "ATIVO",
            },
        )


class TestMedicoControllerCU4CU5(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = MedicoController()
        self.grade_ok = [_criar_grade(DiaSemana.SEGUNDA, time(8, 0), time(12, 0))]

    @patch.object(Especialidade, "listarTodas")
    def test_cu4_listar_especialidades(self, mock_listar: MagicMock) -> None:
        mock_listar.return_value = [_criar_especialidade(1, "Cardiologia")]
        lista = self.controller.listarEspecialidades()
        self.assertEqual(len(lista), 1)
        self.assertEqual(lista[0].getNome(), "Cardiologia")

    def test_cu4_dados_invalidos_ou_grade_incoerente(self) -> None:
        self.assertEqual(
            self.controller.cadastrarMedico("", "12345", "RS", 1, self.grade_ok),
            "Dados inválidos ou grade incoerente",
        )
        self.assertEqual(
            self.controller.cadastrarMedico("Dr. House", "12345", "XX", 1, self.grade_ok),
            "Dados inválidos ou grade incoerente",
        )
        self.assertEqual(
            self.controller.cadastrarMedico("Dr. House", "12345", "RS", 1, []),
            "Dados inválidos ou grade incoerente",
        )
        grade_ruim = [_criar_grade(DiaSemana.SEGUNDA, time(14, 0), time(12, 0))]
        self.assertEqual(
            self.controller.cadastrarMedico("Dr. House", "12345", "RS", 1, grade_ruim),
            "Dados inválidos ou grade incoerente",
        )
        grade_dup = [
            _criar_grade(DiaSemana.SEGUNDA, time(8, 0), time(12, 0)),
            _criar_grade(DiaSemana.SEGUNDA, time(14, 0), time(18, 0)),
        ]
        self.assertEqual(
            self.controller.cadastrarMedico("Dr. House", "12345", "RS", 1, grade_dup),
            "Dados inválidos ou grade incoerente",
        )

    @patch.object(Medico, "existeCrmUf", return_value=True)
    def test_cu4_crm_ja_cadastrado_rn02(self, mock_existe: MagicMock) -> None:
        msg = self.controller.cadastrarMedico("Dr. House", "12345", "rs", 1, self.grade_ok)
        mock_existe.assert_called_once_with("12345", "RS", 0)
        self.assertEqual(msg, "CRM já cadastrado no sistema")

    @patch.object(Medico, "salvar", return_value=True)
    @patch.object(Especialidade, "buscarPorId")
    @patch.object(Medico, "existeCrmUf", return_value=False)
    def test_cu4_cadastrar_medico_sucesso(
        self,
        mock_existe: MagicMock,
        mock_esp: MagicMock,
        mock_salvar: MagicMock,
    ) -> None:
        mock_esp.return_value = _criar_especialidade(1, "Cardiologia")
        msg = self.controller.cadastrarMedico("Dr. Carlos", "54321", "rs", 1, self.grade_ok)
        mock_existe.assert_called_once_with("54321", "RS", 0)
        mock_esp.assert_called_once_with(1)
        mock_salvar.assert_called_once()
        self.assertEqual(msg, "Médico cadastrado com sucesso!")

    @patch.object(Medico, "existeCrmUf", return_value=True)
    def test_cu5_validar_medico_crm_duplicado(self, mock_existe: MagicMock) -> None:
        erro = self.controller.validarMedico(
            10, "Dr. Carlos", "54321", "RS", 1, self.grade_ok, Situacao.ATIVO
        )
        mock_existe.assert_called_once_with("54321", "RS", 10)
        self.assertEqual(erro, "CRM já cadastrado no sistema")

    @patch.object(Medico, "existeCrmUf", return_value=False)
    def test_cu5_validar_medico_ok(self, mock_existe: MagicMock) -> None:
        erro = self.controller.validarMedico(
            10, "Dr. Carlos", "54321", "RS", 1, self.grade_ok, Situacao.INATIVO
        )
        mock_existe.assert_called_once_with("54321", "RS", 10)
        self.assertIsNone(erro)

    @patch.object(Medico, "salvar", return_value=True)
    @patch.object(Especialidade, "buscarPorId")
    @patch.object(Medico, "buscarPorId")
    @patch.object(Medico, "existeCrmUf", return_value=False)
    def test_cu5_editar_medico_sucesso(
        self,
        mock_existe: MagicMock,
        mock_buscar_med: MagicMock,
        mock_buscar_esp: MagicMock,
        mock_salvar: MagicMock,
    ) -> None:
        med = Medico()
        med.setId(10)
        med.setNome("Dr. Antigo")
        med.setCrm("54321")
        med.setUfCrm("RS")
        med.setEspecialidade(_criar_especialidade(1, "Cardiologia"))
        med.setSituacao(Situacao.ATIVO)
        med.setGrades(self.grade_ok)

        nova_esp = _criar_especialidade(2, "Neurologia")
        mock_buscar_med.return_value = med
        mock_buscar_esp.return_value = nova_esp

        nova_grade = [_criar_grade(DiaSemana.QUARTA, time(9, 0), time(17, 0))]
        msg = self.controller.editarMedico(
            10, "Dr. Novo", "54321", "SP", 2, nova_grade, Situacao.INATIVO
        )
        self.assertEqual(msg, "Médico atualizado com sucesso!")
        self.assertEqual(med.getNome(), "Dr. Novo")
        self.assertEqual(med.getUfCrm(), "SP")
        self.assertIs(med.getEspecialidade(), nova_esp)
        self.assertEqual(med.getSituacao(), Situacao.INATIVO)
        self.assertEqual(med.getGrades()[0].getDiaSemana(), DiaSemana.QUARTA)
        mock_salvar.assert_called_once()


class TestPacienteControllerCU6CU7(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = PacienteController()
        self.nasc_valido = date(1995, 3, 20)

    def test_cu6_dados_invalidos(self) -> None:
        # CPF com menos de 11 dígitos
        self.assertEqual(
            self.controller.cadastrarPaciente("12345", "Ana", self.nasc_valido, Sexo.FEMININO, "51999990000"),
            "Dados inválidos",
        )
        # Data de nascimento futura
        amanha = self.controller._hoje_clinica() + timedelta(days=1)
        self.assertEqual(
            self.controller.cadastrarPaciente("12345678901", "Ana", amanha, Sexo.FEMININO, "51999990000"),
            "Dados inválidos",
        )
        # Nome vazio
        self.assertEqual(
            self.controller.cadastrarPaciente("12345678901", "  ", self.nasc_valido, Sexo.FEMININO, "51999990000"),
            "Dados inválidos",
        )

    @patch.object(Paciente, "buscarPorCpf")
    def test_cu6_cpf_duplicado_exibe_nome_e_situacao_rn01(self, mock_buscar: MagicMock) -> None:
        existente = Paciente()
        existente.setId(3)
        existente.setCpf("12345678901")
        existente.setNome("Maria Clara")
        existente.setSituacao(Situacao.INATIVO)
        mock_buscar.return_value = existente

        msg = self.controller.cadastrarPaciente(
            "123.456.789-01", "Outra Pessoa", self.nasc_valido, Sexo.FEMININO, "51988887777"
        )
        mock_buscar.assert_called_once_with("12345678901")
        self.assertEqual(msg, "CPF já cadastrado no sistema: Maria Clara (Inativo)")

    @patch.object(Paciente, "salvar", return_value=True)
    @patch.object(Paciente, "buscarPorCpf", return_value=None)
    def test_cu6_cadastrar_paciente_sucesso(
        self, mock_buscar: MagicMock, mock_salvar: MagicMock
    ) -> None:
        msg = self.controller.cadastrarPaciente(
            "123.456.789-01", "Maria Clara", self.nasc_valido, Sexo.FEMININO, "(51) 98888-7777"
        )
        mock_buscar.assert_called_once_with("12345678901")
        mock_salvar.assert_called_once()
        self.assertEqual(msg, "Paciente cadastrado com sucesso!")

    @patch.object(Paciente, "buscarPorFiltro")
    def test_cu7_consultar_pacientes(self, mock_filtro: MagicMock) -> None:
        self.assertEqual(self.controller.consultarPacientes("   "), [])
        mock_filtro.assert_not_called()

        pac = Paciente()
        pac.setId(1)
        pac.setNome("Maria Clara")
        mock_filtro.return_value = [pac]
        res = self.controller.consultarPacientes("Maria")
        mock_filtro.assert_called_once_with("Maria")
        self.assertEqual(len(res), 1)

    def test_cu7_validar_paciente(self) -> None:
        amanha = self.controller._hoje_clinica() + timedelta(days=1)
        self.assertEqual(
            self.controller.validarPaciente(1, "Ana", amanha, Sexo.FEMININO, "5199999", Situacao.ATIVO),
            "Dados inválidos",
        )
        self.assertIsNone(
            self.controller.validarPaciente(
                1, "Ana", self.nasc_valido, Sexo.FEMININO, "5199999", Situacao.INATIVO
            )
        )

    @patch.object(Paciente, "salvar", return_value=True)
    @patch.object(Paciente, "buscarPorId")
    def test_cu7_editar_paciente_sucesso_sem_alterar_cpf(
        self, mock_buscar: MagicMock, mock_salvar: MagicMock
    ) -> None:
        pac = Paciente()
        pac.setId(4)
        pac.setCpf("99988877766")
        pac.setNome("Maria Antiga")
        pac.setDataNascimento(date(1990, 1, 1))
        pac.setSexo(Sexo.FEMININO)
        pac.setTelefone("5100000000")
        pac.setSituacao(Situacao.INATIVO)
        mock_buscar.return_value = pac

        msg = self.controller.editarPaciente(
            4, "Maria Reativada", date(1990, 1, 2), Sexo.FEMININO, "(51) 91234-5678", Situacao.ATIVO
        )
        self.assertEqual(msg, "Dados do paciente atualizados com sucesso!")
        self.assertEqual(pac.getCpf(), "99988877766")
        self.assertEqual(pac.getNome(), "Maria Reativada")
        self.assertEqual(pac.getSituacao(), Situacao.ATIVO)
        mock_salvar.assert_called_once()


class TestHttpApiCiclo2(unittest.TestCase):
    """Valida as rotas HTTP do Ciclo 2 e o controle de acesso por perfil."""

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

    def test_fluxo_api_medicos_e_controle_acesso(self) -> None:
        token_admin = self._autenticar(Perfil.ADMINISTRADOR)
        token_rec = self._autenticar(Perfil.RECEPCIONISTA)

        # Recepcionista não acessa CRUD de médicos (403)
        status, _ = self._req("GET", "/api/medicos", token=token_rec)
        self.assertEqual(status, 403)

        esp = _criar_especialidade(1, "Cardiologia")
        with patch.object(Especialidade, "listarTodas", return_value=[esp]):
            status, dados = self._req("GET", "/api/especialidades", token=token_admin)
            self.assertEqual(status, 200)
            self.assertEqual(len(dados["especialidades"]), 1)

        payload_medico = {
            "nome": "Dr. João",
            "crm": "112233",
            "ufCrm": "RS",
            "especialidadeId": 1,
            "grades": [{"diaSemana": "SEGUNDA", "horaInicial": "08:00", "horaFinal": "12:00"}],
        }

        with patch.object(Medico, "existeCrmUf", return_value=True):
            status, dados = self._req("POST", "/api/medicos", payload_medico, token=token_admin)
            self.assertEqual(status, 409)
            self.assertEqual(dados["mensagem"], "CRM já cadastrado no sistema")

        with patch.object(Medico, "existeCrmUf", return_value=False), patch.object(
            Especialidade, "buscarPorId", return_value=esp
        ), patch.object(Medico, "salvar", return_value=True):
            status, dados = self._req("POST", "/api/medicos", payload_medico, token=token_admin)
            self.assertEqual(status, 201)
            self.assertEqual(dados["mensagem"], "Médico cadastrado com sucesso!")

        # Validação antes da confirmação (CU5)
        payload_edicao = {**payload_medico, "situacao": "INATIVO"}
        with patch.object(Medico, "existeCrmUf", return_value=False):
            status, dados = self._req(
                "POST", "/api/medicos/10/validar", payload_edicao, token=token_admin
            )
            self.assertEqual(status, 200)
            self.assertTrue(dados["valido"])

        med_obj = Medico()
        med_obj.setId(10)
        med_obj.setNome("Dr. João")
        med_obj.setCrm("112233")
        med_obj.setUfCrm("RS")
        med_obj.setEspecialidade(esp)
        med_obj.setSituacao(Situacao.ATIVO)
        med_obj.setGrades([_criar_grade(DiaSemana.SEGUNDA, time(8, 0), time(12, 0))])

        with patch.object(Medico, "buscarPorId", return_value=med_obj):
            status, dados = self._req("GET", "/api/medicos/10", token=token_admin)
            self.assertEqual(status, 200)
            self.assertEqual(dados["medico"]["crm"], "112233")

        with patch.object(Medico, "existeCrmUf", return_value=False), patch.object(
            Medico, "buscarPorId", return_value=med_obj
        ), patch.object(Especialidade, "buscarPorId", return_value=esp), patch.object(
            Medico, "salvar", return_value=True
        ):
            status, dados = self._req("PUT", "/api/medicos/10", payload_edicao, token=token_admin)
            self.assertEqual(status, 200)
            self.assertEqual(dados["mensagem"], "Médico atualizado com sucesso!")

    def test_fluxo_api_pacientes_e_controle_acesso(self) -> None:
        token_admin = self._autenticar(Perfil.ADMINISTRADOR)
        token_rec = self._autenticar(Perfil.RECEPCIONISTA)

        # Administrador não acessa CRUD de pacientes (403)
        status, _ = self._req("GET", "/api/pacientes?termo=Ana", token=token_admin)
        self.assertEqual(status, 403)

        payload_pac = {
            "cpf": "123.456.789-01",
            "nome": "Ana Beatriz",
            "dataNascimento": "1992-08-10",
            "sexo": "FEMININO",
            "telefone": "(51) 99999-2222",
        }

        existente = Paciente()
        existente.setId(5)
        existente.setCpf("12345678901")
        existente.setNome("Ana Beatriz")
        existente.setDataNascimento(date(1992, 8, 10))
        existente.setSexo(Sexo.FEMININO)
        existente.setTelefone("(51) 99999-2222")
        existente.setSituacao(Situacao.ATIVO)

        with patch.object(Paciente, "buscarPorCpf", return_value=existente):
            status, dados = self._req("POST", "/api/pacientes", payload_pac, token=token_rec)
            self.assertEqual(status, 409)
            self.assertEqual(dados["mensagem"], "CPF já cadastrado no sistema: Ana Beatriz (Ativo)")

        with patch.object(Paciente, "buscarPorCpf", return_value=None), patch.object(
            Paciente, "salvar", return_value=True
        ):
            status, dados = self._req("POST", "/api/pacientes", payload_pac, token=token_rec)
            self.assertEqual(status, 201)
            self.assertEqual(dados["mensagem"], "Paciente cadastrado com sucesso!")

        with patch.object(Paciente, "buscarPorFiltro", return_value=[existente]):
            status, dados = self._req("GET", "/api/pacientes?termo=Ana", token=token_rec)
            self.assertEqual(status, 200)
            self.assertEqual(len(dados["pacientes"]), 1)

        payload_edicao = {
            "nome": "Ana Beatriz Souza",
            "dataNascimento": "1992-08-10",
            "sexo": "FEMININO",
            "telefone": "(51) 98888-0000",
            "situacao": "INATIVO",
        }
        status, dados = self._req(
            "POST", "/api/pacientes/5/validar", payload_edicao, token=token_rec
        )
        self.assertEqual(status, 200)
        self.assertTrue(dados["valido"])

        with patch.object(Paciente, "buscarPorId", return_value=existente), patch.object(
            Paciente, "salvar", return_value=True
        ):
            status, dados = self._req("PUT", "/api/pacientes/5", payload_edicao, token=token_rec)
            self.assertEqual(status, 200)
            self.assertEqual(dados["mensagem"], "Dados do paciente atualizados com sucesso!")


if __name__ == "__main__":
    unittest.main()
