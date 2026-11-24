"""Testes unitários do Ciclo 1 (UC1, UC2, UC3) sem dependência de conexão real ao MySQL."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from controller.auth_controller import AuthController
from controller.recepcionista_controller import RecepcionistaController
from model.perfil import Perfil
from model.usuario import Usuario


class TestUsuarioModel(unittest.TestCase):
    def test_getters_setters_e_ausencia_de_get_senha(self) -> None:
        usuario = Usuario()
        usuario.setId(10)
        usuario.setNome("Maria Silva")
        usuario.setLogin("maria")
        usuario.setSenha("segredo123")
        usuario.setPerfil(Perfil.RECEPCIONISTA)

        self.assertEqual(usuario.getId(), 10)
        self.assertEqual(usuario.getNome(), "Maria Silva")
        self.assertEqual(usuario.getLogin(), "maria")
        self.assertEqual(usuario.getPerfil(), Perfil.RECEPCIONISTA)
        self.assertFalse(hasattr(usuario, "getSenha"))

    def test_hash_e_verificacao_senha_padrao_schema(self) -> None:
        hash_admin = (
            "pbkdf2_sha256$100000$a1b2c3d4e5f60718293a4b5c6d7e8f90$"
            "44138abc921d1c95bb573a09516cd4c82e8271fc3d9604b7c5f7f1bf26b6292d"
        )
        self.assertTrue(Usuario._verificar_senha("admin123", hash_admin))
        self.assertFalse(Usuario._verificar_senha("errada", hash_admin))


class TestAuthControllerCU1(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = AuthController()

    def test_entrar_com_campos_vazios_retorna_none(self) -> None:
        self.assertIsNone(self.controller.entrar("", "123"))
        self.assertIsNone(self.controller.entrar("admin", ""))

    @patch.object(Usuario, "autenticar")
    def test_entrar_sucesso_retorna_usuario(self, mock_autenticar: MagicMock) -> None:
        esperado = Usuario()
        esperado.setId(1)
        esperado.setNome("Administrador")
        esperado.setLogin("admin")
        esperado.setPerfil(Perfil.ADMINISTRADOR)
        mock_autenticar.return_value = esperado

        resultado = self.controller.entrar("  admin  ", "admin123")
        mock_autenticar.assert_called_once_with("admin", "admin123")
        self.assertIs(resultado, esperado)

    @patch.object(Usuario, "autenticar", return_value=None)
    def test_entrar_credenciais_invalidas_retorna_none(self, mock_autenticar: MagicMock) -> None:
        resultado = self.controller.entrar("admin", "senha_errada")
        self.assertIsNone(resultado)


class TestRecepcionistaControllerCU2CU3(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = RecepcionistaController()

    def test_cu2_campos_obrigatorios_vazios(self) -> None:
        msg = self.controller.cadastrarRecepcionista("", "ana", "123456")
        self.assertEqual(msg, "Preencha todos os campos obrigatórios")

        msg2 = self.controller.cadastrarRecepcionista("Ana", "   ", "123456")
        self.assertEqual(msg2, "Preencha todos os campos obrigatórios")

        msg3 = self.controller.cadastrarRecepcionista("Ana", "ana", "")
        self.assertEqual(msg3, "Preencha todos os campos obrigatórios")

    @patch.object(Usuario, "existeLogin", return_value=True)
    def test_cu2_login_ja_utilizado_rn11(self, mock_existe: MagicMock) -> None:
        msg = self.controller.cadastrarRecepcionista("Ana Paula", "admin", "123456")
        mock_existe.assert_called_once_with("admin")
        self.assertEqual(msg, "Login já utilizado")

    @patch.object(Usuario, "salvar", return_value=True)
    @patch.object(Usuario, "existeLogin", return_value=False)
    def test_cu2_cadastro_sucesso(self, mock_existe: MagicMock, mock_salvar: MagicMock) -> None:
        msg = self.controller.cadastrarRecepcionista("Ana Paula", "ana.paula", "senha123")
        mock_existe.assert_called_once_with("ana.paula")
        mock_salvar.assert_called_once()
        self.assertEqual(msg, "Recepcionista cadastrada com sucesso!")

    @patch.object(Usuario, "listarRecepcionistas")
    def test_cu3_listar_recepcionistas(self, mock_listar: MagicMock) -> None:
        rec = Usuario()
        rec.setId(2)
        rec.setNome("Carla")
        rec.setLogin("carla")
        rec.setPerfil(Perfil.RECEPCIONISTA)
        mock_listar.return_value = [rec]

        lista = self.controller.listarRecepcionistas()
        self.assertEqual(len(lista), 1)
        self.assertEqual(lista[0].getLogin(), "carla")

    def test_cu3_editar_dados_invalidos(self) -> None:
        self.assertEqual(self.controller.editarRecepcionista(0, "Carla", ""), "Dados inválidos")
        self.assertEqual(self.controller.editarRecepcionista(2, "   ", ""), "Dados inválidos")

    @patch.object(Usuario, "buscarPorId")
    def test_cu3_editar_recusa_editar_administrador(self, mock_buscar: MagicMock) -> None:
        admin = Usuario()
        admin.setId(1)
        admin.setNome("Admin")
        admin.setLogin("admin")
        admin.setPerfil(Perfil.ADMINISTRADOR)
        mock_buscar.return_value = admin

        msg = self.controller.editarRecepcionista(1, "Novo Nome", "")
        self.assertEqual(msg, "Dados inválidos")

    @patch.object(Usuario, "salvar", return_value=True)
    @patch.object(Usuario, "buscarPorId")
    def test_cu3_editar_sucesso_com_e_sem_nova_senha(
        self, mock_buscar: MagicMock, mock_salvar: MagicMock
    ) -> None:
        rec = Usuario()
        rec.setId(2)
        rec.setNome("Carla Antiga")
        rec.setLogin("carla")
        rec.setPerfil(Perfil.RECEPCIONISTA)
        mock_buscar.return_value = rec

        msg = self.controller.editarRecepcionista(2, "Carla Atualizada", "")
        self.assertEqual(msg, "Recepcionista atualizada com sucesso!")
        self.assertEqual(rec.getNome(), "Carla Atualizada")
        mock_salvar.assert_called_once()

        msg2 = self.controller.editarRecepcionista(2, "Carla Nova", "novaSenha99")
        self.assertEqual(msg2, "Recepcionista atualizada com sucesso!")
        self.assertEqual(rec.getNome(), "Carla Nova")
        self.assertEqual(mock_salvar.call_count, 2)


class TestHttpApiCiclo1(unittest.TestCase):
    """Valida as rotas HTTP do servidor Python puro (http.server)."""

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

    def test_health_endpoint(self) -> None:
        status, dados = self._req("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(dados["status"], "ok")

    @patch.object(Usuario, "autenticar")
    def test_fluxo_autenticacao_e_controle_de_acesso(self, mock_autenticar: MagicMock) -> None:
        # 1. Falha de login -> 401
        mock_autenticar.return_value = None
        status, dados = self._req("POST", "/api/auth/entrar", {"login": "admin", "senha": "errada"})
        self.assertEqual(status, 401)
        self.assertEqual(dados["mensagem"], "Login ou senha inválidos")

        # 2. Acesso sem token -> 401
        status, _ = self._req("GET", "/api/recepcionistas")
        self.assertEqual(status, 401)

        # 3. Login como Recepcionista -> acesso negado (403) ao CRUD de recepcionistas
        rec = Usuario()
        rec.setId(2)
        rec.setNome("Ana")
        rec.setLogin("ana")
        rec.setPerfil(Perfil.RECEPCIONISTA)
        mock_autenticar.return_value = rec

        status, dados = self._req("POST", "/api/auth/entrar", {"login": "ana", "senha": "123"})
        self.assertEqual(status, 200)
        token_rec = dados["token"]
        status, _ = self._req("GET", "/api/recepcionistas", token=token_rec)
        self.assertEqual(status, 403)

        # 4. Login como Administrador -> 200 e acesso permitido
        admin = Usuario()
        admin.setId(1)
        admin.setNome("Administrador")
        admin.setLogin("admin")
        admin.setPerfil(Perfil.ADMINISTRADOR)
        mock_autenticar.return_value = admin

        status, dados = self._req("POST", "/api/auth/entrar", {"login": "admin", "senha": "admin123"})
        self.assertEqual(status, 200)
        token_admin = dados["token"]

        with patch.object(Usuario, "listarRecepcionistas", return_value=[rec]):
            status, dados = self._req("GET", "/api/recepcionistas", token=token_admin)
            self.assertEqual(status, 200)
            self.assertEqual(len(dados["recepcionistas"]), 1)

        with patch.object(Usuario, "existeLogin", return_value=True):
            status, dados = self._req(
                "POST",
                "/api/recepcionistas",
                {"nome": "Nova", "login": "ana", "senha": "123"},
                token=token_admin,
            )
            self.assertEqual(status, 409)
            self.assertEqual(dados["mensagem"], "Login já utilizado")

        with patch.object(Usuario, "existeLogin", return_value=False), patch.object(
            Usuario, "salvar", return_value=True
        ):
            status, dados = self._req(
                "POST",
                "/api/recepcionistas",
                {"nome": "Beatriz", "login": "bia", "senha": "123"},
                token=token_admin,
            )
            self.assertEqual(status, 201)
            self.assertEqual(dados["mensagem"], "Recepcionista cadastrada com sucesso!")

        with patch.object(Usuario, "buscarPorId", return_value=rec), patch.object(
            Usuario, "salvar", return_value=True
        ):
            status, dados = self._req(
                "PUT",
                "/api/recepcionistas/2",
                {"nome": "Ana Maria", "novaSenha": ""},
                token=token_admin,
            )
            self.assertEqual(status, 200)
            self.assertEqual(dados["mensagem"], "Recepcionista atualizada com sucesso!")

        # 5. Logout invalida o token
        status, _ = self._req("POST", "/api/auth/sair", token=token_admin)
        self.assertEqual(status, 200)
        status, _ = self._req("GET", "/api/auth/sessao", token=token_admin)
        self.assertEqual(status, 401)


if __name__ == "__main__":
    unittest.main()
