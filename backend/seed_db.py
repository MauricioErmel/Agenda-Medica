"""Script utilitário para popular o banco de dados com dados fictícios realistas.

Uso:
    python backend/seed_db.py          # Insere dados que ainda não existem (idempotente)
    python backend/seed_db.py --reset  # Limpa os dados (exceto especialidades e admin) e repopula
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional, Tuple

import config
from database import Database
from init_db import inicializar_banco
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


def _gerar_cpf_valido(base_nove_digitos: str) -> str:
    """Gera um CPF válido de 11 dígitos a partir de 9 dígitos base."""
    digitos = [int(d) for d in base_nove_digitos]
    soma1 = sum(d * peso for d, peso in zip(digitos, range(10, 1, -1)))
    resto1 = (soma1 * 10) % 11
    dv1 = 0 if resto1 == 10 else resto1
    digitos.append(dv1)

    soma2 = sum(d * peso for d, peso in zip(digitos, range(11, 1, -1)))
    resto2 = (soma2 * 10) % 11
    dv2 = 0 if resto2 == 10 else resto2
    digitos.append(dv2)

    return "".join(str(d) for d in digitos)


def _limpar_dados_existentes() -> None:
    """Remove dados transacionais e cadastrais mantendo especialidades e o usuário admin."""
    conexao = Database.get_connection()
    try:
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM ausencias")
        cursor.execute("DELETE FROM consultas")
        cursor.execute("DELETE FROM grades_atendimento")
        cursor.execute("DELETE FROM medicos")
        cursor.execute("DELETE FROM pacientes")
        cursor.execute("DELETE FROM usuarios WHERE login <> 'admin'")
        conexao.commit()
        cursor.close()
        print("Dados anteriores removidos (especialidades e usuário 'admin' preservados).")
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def _seed_usuarios() -> Tuple[int, int]:
    """Cria usuários administradores e recepcionistas se ainda não existirem."""
    usuarios_dados = [
        ("Coordenação Clínica", "coord.clinica", "admin123", Perfil.ADMINISTRADOR),
        ("Ana Paula Ferreira", "recepcao1", "recepcao123", Perfil.RECEPCIONISTA),
        ("Bruno Henrique Costa", "recepcao2", "recepcao123", Perfil.RECEPCIONISTA),
        ("Carla Mendes", "carla.recepcao", "recepcao123", Perfil.RECEPCIONISTA),
        ("Lucas Almeida", "lucas.recepcao", "recepcao123", Perfil.RECEPCIONISTA),
    ]

    criados = 0
    ignorados = 0
    for nome, login, senha, perfil in usuarios_dados:
        if Usuario.existeLogin(login):
            ignorados += 1
            continue
        usuario = Usuario()
        usuario.setNome(nome)
        usuario.setLogin(login)
        usuario.setSenha(senha)
        usuario.setPerfil(perfil)
        usuario.salvar()
        criados += 1

    return criados, ignorados


def _criar_grade(dia: DiaSemana, inicio: time, fim: time) -> GradeAtendimento:
    grade = GradeAtendimento()
    grade.setDiaSemana(dia)
    grade.setHoraInicial(inicio)
    grade.setHoraFinal(fim)
    return grade


def _seed_medicos() -> Tuple[List[Medico], int, int]:
    """Cria médicos com suas especialidades e grades de atendimento."""
    especialidades_por_nome: Dict[str, Especialidade] = {
        esp.getNome(): esp for esp in Especialidade.listarTodas()
    }

    medicos_dados = [
        {
            "nome": "Dr. Ricardo Silveira",
            "crm": "10452",
            "uf": "RS",
            "especialidade": "Cardiologia",
            "situacao": Situacao.ATIVO,
            "grades": [
                _criar_grade(DiaSemana.SEGUNDA, time(8, 0), time(12, 0)),
                _criar_grade(DiaSemana.QUARTA, time(8, 0), time(12, 0)),
                _criar_grade(DiaSemana.SEXTA, time(13, 30), time(17, 30)),
            ],
        },
        {
            "nome": "Dra. Mariana Vasconcelos",
            "crm": "22890",
            "uf": "RS",
            "especialidade": "Clínica Geral",
            "situacao": Situacao.ATIVO,
            "grades": [
                _criar_grade(DiaSemana.SEGUNDA, time(8, 0), time(12, 0)),
                _criar_grade(DiaSemana.TERCA, time(8, 0), time(12, 0)),
                _criar_grade(DiaSemana.QUINTA, time(13, 0), time(17, 0)),
                _criar_grade(DiaSemana.SEXTA, time(8, 0), time(12, 0)),
            ],
        },
        {
            "nome": "Dra. Camila Nogueira",
            "crm": "31944",
            "uf": "RS",
            "especialidade": "Dermatologia",
            "situacao": Situacao.ATIVO,
            "grades": [
                _criar_grade(DiaSemana.TERCA, time(13, 30), time(18, 0)),
                _criar_grade(DiaSemana.QUINTA, time(8, 30), time(12, 30)),
            ],
        },
        {
            "nome": "Dr. Eduardo Tavares",
            "crm": "18731",
            "uf": "RS",
            "especialidade": "Ortopedia e Traumatologia",
            "situacao": Situacao.ATIVO,
            "grades": [
                _criar_grade(DiaSemana.SEGUNDA, time(13, 30), time(17, 30)),
                _criar_grade(DiaSemana.QUARTA, time(13, 30), time(17, 30)),
                _criar_grade(DiaSemana.SABADO, time(8, 0), time(12, 0)),
            ],
        },
        {
            "nome": "Dra. Fernanda Ribeiro",
            "crm": "27510",
            "uf": "RS",
            "especialidade": "Pediatria",
            "situacao": Situacao.ATIVO,
            "grades": [
                _criar_grade(DiaSemana.SEGUNDA, time(9, 0), time(12, 0)),
                _criar_grade(DiaSemana.TERCA, time(9, 0), time(12, 0)),
                _criar_grade(DiaSemana.QUARTA, time(9, 0), time(12, 0)),
                _criar_grade(DiaSemana.QUINTA, time(9, 0), time(12, 0)),
            ],
        },
        {
            "nome": "Dr. Gustavo Monteiro",
            "crm": "34219",
            "uf": "RS",
            "especialidade": "Neurologia",
            "situacao": Situacao.ATIVO,
            "grades": [
                _criar_grade(DiaSemana.TERCA, time(14, 0), time(18, 0)),
                _criar_grade(DiaSemana.SEXTA, time(8, 30), time(12, 30)),
            ],
        },
        {
            "nome": "Dra. Beatriz Lopes",
            "crm": "29876",
            "uf": "RS",
            "especialidade": "Ginecologia e Obstetrícia",
            "situacao": Situacao.ATIVO,
            "grades": [
                _criar_grade(DiaSemana.QUARTA, time(8, 0), time(12, 0)),
                _criar_grade(DiaSemana.QUINTA, time(14, 0), time(18, 0)),
            ],
        },
        {
            "nome": "Dr. Rafael Souza",
            "crm": "41005",
            "uf": "SP",
            "especialidade": "Oftalmologia",
            "situacao": Situacao.ATIVO,
            "grades": [
                _criar_grade(DiaSemana.SEGUNDA, time(14, 0), time(18, 0)),
                _criar_grade(DiaSemana.SEXTA, time(14, 0), time(18, 0)),
            ],
        },
        {
            "nome": "Dra. Juliana Prado",
            "crm": "15678",
            "uf": "RS",
            "especialidade": "Psiquiatria",
            "situacao": Situacao.INATIVO,
            "grades": [
                _criar_grade(DiaSemana.QUARTA, time(14, 0), time(17, 0)),
            ],
        },
    ]

    criados = 0
    ignorados = 0
    for item in medicos_dados:
        if Medico.existeCrmUf(item["crm"], item["uf"]):
            ignorados += 1
            continue

        especialidade = especialidades_por_nome.get(item["especialidade"])
        if especialidade is None:
            continue

        medico = Medico()
        medico.setNome(item["nome"])
        medico.setCrm(item["crm"])
        medico.setUfCrm(item["uf"])
        medico.setEspecialidade(especialidade)
        medico.setSituacao(item["situacao"])
        medico.setGrades(item["grades"])
        medico.salvar()
        criados += 1

    return Medico.listarTodos(), criados, ignorados


def _seed_pacientes() -> Tuple[List[Paciente], int, int]:
    """Cria pacientes ativos e inativos com CPFs válidos."""
    pacientes_dados = [
        ("100200301", "João Pedro Martins", date(1985, 3, 14), Sexo.MASCULINO, "(51) 99123-4501", Situacao.ATIVO),
        ("100200302", "Maria Clara Oliveira", date(1992, 7, 22), Sexo.FEMININO, "(51) 99234-5602", Situacao.ATIVO),
        ("100200303", "Carlos Eduardo Lima", date(1978, 11, 5), Sexo.MASCULINO, "(51) 99345-6703", Situacao.ATIVO),
        ("100200304", "Fernanda Rodrigues", date(1990, 1, 19), Sexo.FEMININO, "(51) 99456-7804", Situacao.ATIVO),
        ("100200305", "Gabriel Santos Rocha", date(2001, 5, 30), Sexo.MASCULINO, "(51) 99567-8905", Situacao.ATIVO),
        ("100200306", "Juliana Azevedo Castro", date(1988, 9, 12), Sexo.FEMININO, "(51) 99678-9006", Situacao.ATIVO),
        ("100200307", "Matheus Henrique Dias", date(1995, 12, 3), Sexo.MASCULINO, "(51) 99789-0107", Situacao.ATIVO),
        ("100200308", "Larissa Fernandes Moura", date(1983, 4, 27), Sexo.FEMININO, "(51) 99890-1208", Situacao.ATIVO),
        ("100200309", "Rafael Augusto Pereira", date(1972, 8, 15), Sexo.MASCULINO, "(51) 98111-2209", Situacao.ATIVO),
        ("100200310", "Patrícia Gomes Barbosa", date(1969, 2, 9), Sexo.FEMININO, "(51) 98222-3310", Situacao.ATIVO),
        ("100200311", "Thiago Moreira Cardoso", date(1998, 6, 18), Sexo.MASCULINO, "(51) 98333-4411", Situacao.ATIVO),
        ("100200312", "Sofia Carvalho Teixeira", date(2015, 10, 25), Sexo.FEMININO, "(51) 98444-5512", Situacao.ATIVO),
        ("100200313", "Leonardo Vieira Ramos", date(2018, 4, 8), Sexo.MASCULINO, "(51) 98555-6613", Situacao.ATIVO),
        ("100200314", "Aline Duarte Correia", date(1993, 11, 17), Sexo.OUTRO, "(51) 98666-7714", Situacao.ATIVO),
        ("100200315", "Roberto Nascimento Pinto", date(1960, 7, 1), Sexo.MASCULINO, "(51) 98777-8815", Situacao.ATIVO),
        ("100200316", "Helena Borges Farias", date(1955, 12, 20), Sexo.FEMININO, "(51) 98888-9916", Situacao.INATIVO),
        ("100200317", "Diego Santana Machado", date(1987, 3, 29), Sexo.MASCULINO, "(51) 98999-0017", Situacao.INATIVO),
    ]

    criados = 0
    ignorados = 0
    pacientes_carregados: List[Paciente] = []

    for base_cpf, nome, nascimento, sexo, telefone, situacao in pacientes_dados:
        cpf = _gerar_cpf_valido(base_cpf)
        existente = Paciente.buscarPorCpf(cpf)
        if existente is not None:
            ignorados += 1
            pacientes_carregados.append(existente)
            continue

        paciente = Paciente()
        paciente.setCpf(cpf)
        paciente.setNome(nome)
        paciente.setDataNascimento(nascimento)
        paciente.setSexo(sexo)
        paciente.setTelefone(telefone)
        paciente.setSituacao(situacao)
        paciente.salvar()
        criados += 1
        pacientes_carregados.append(paciente)

    return pacientes_carregados, criados, ignorados


def _existe_ausencia(medico_id: int, data_inicial: date, data_final: date) -> bool:
    conexao = Database.get_connection()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            """
            SELECT 1 FROM ausencias
            WHERE medico_id = %s AND data_inicial = %s AND data_final = %s
            LIMIT 1
            """,
            (medico_id, data_inicial, data_final),
        )
        existe = cursor.fetchone() is not None
        cursor.close()
        return existe
    finally:
        conexao.close()


def _seed_ausencias(medicos: List[Medico], hoje: date) -> Tuple[int, int]:
    """Cria ausências médicas passadas e futuras para testes do Ciclo 4."""
    medicos_ativos = [m for m in medicos if m.getSituacao() == Situacao.ATIVO]
    if len(medicos_ativos) < 3:
        return 0, 0

    ausencias_planejadas = [
        (medicos_ativos[0], "Congresso Brasileiro de Cardiologia", hoje + timedelta(days=15), hoje + timedelta(days=17)),
        (medicos_ativos[1], "Férias programadas", hoje + timedelta(days=22), hoje + timedelta(days=26)),
        (medicos_ativos[2], "Simpósio de Atualização Médica", hoje - timedelta(days=10), hoje - timedelta(days=9)),
    ]

    criadas = 0
    ignoradas = 0
    for medico, motivo, inicio, fim in ausencias_planejadas:
        if medico.getId() is None:
            continue
        if _existe_ausencia(medico.getId(), inicio, fim):
            ignoradas += 1
            continue
        ausencia = Ausencia()
        ausencia.setMedico(medico)
        ausencia.setMotivo(motivo)
        ausencia.setDataInicial(inicio)
        ausencia.setDataFinal(fim)
        ausencia.salvar()
        criadas += 1

    return criadas, ignoradas


def _existe_consulta(medico_id: int, paciente_id: int, data_hora: datetime) -> bool:
    conexao = Database.get_connection()
    try:
        cursor = conexao.cursor()
        cursor.execute(
            """
            SELECT 1 FROM consultas
            WHERE medico_id = %s AND paciente_id = %s AND data_hora = %s
            LIMIT 1
            """,
            (medico_id, paciente_id, data_hora),
        )
        existe = cursor.fetchone() is not None
        cursor.close()
        return existe
    finally:
        conexao.close()


def _proximo_slot_disponivel(
    medico: Medico,
    data_inicio: date,
    duracao_minutos: int,
    slot_idx: int,
    passo_dias: int = 1,
    limite_dias: int = 21,
) -> Optional[datetime]:
    """Encontra uma data/hora válida dentro da grade do médico e sem ausência."""
    for deslocamento in range(0, limite_dias):
        data_alvo = data_inicio + timedelta(days=deslocamento * passo_dias)
        grade = medico.getGradeDoDia(data_alvo)
        if grade is None:
            continue
        if medico.getId() is not None and Ausencia.existeAusenciaNaData(medico.getId(), data_alvo):
            continue
        horarios = grade.gerarHorarios(duracao_minutos)
        if not horarios:
            continue
        horario = horarios[slot_idx % len(horarios)]
        return datetime.combine(data_alvo, horario)
    return None


def _seed_consultas(
    medicos: List[Medico],
    pacientes: List[Paciente],
    agora: datetime,
) -> Tuple[int, int]:
    """Cria consultas passadas, futuras, canceladas e com lembretes pendentes/enviados."""
    medicos_ativos = [m for m in medicos if m.getSituacao() == Situacao.ATIVO and m.getId() is not None]
    pacientes_ativos = [p for p in pacientes if p.getSituacao() == Situacao.ATIVO and p.getId() is not None]
    if not medicos_ativos or not pacientes_ativos:
        return 0, 0

    duracao = config.CONSULTA_DURACAO_MINUTOS
    hoje = agora.date()

    # Planejamento: (indice_medico, indice_paciente, data_base, passo_dias, slot_idx, status, lembrete, motivo)
    planos = [
        # Consultas futuras (próximos 14 dias) - mix de lembretes PENDENTE e ENVIADO
        (0, 0, hoje + timedelta(days=1), 1, 0, StatusConsulta.AGENDADA, StatusLembrete.PENDENTE, None),
        (0, 1, hoje + timedelta(days=1), 1, 1, StatusConsulta.AGENDADA, StatusLembrete.ENVIADO, None),
        (0, 2, hoje + timedelta(days=3), 1, 2, StatusConsulta.AGENDADA, StatusLembrete.PENDENTE, None),
        (1, 3, hoje + timedelta(days=1), 1, 0, StatusConsulta.AGENDADA, StatusLembrete.PENDENTE, None),
        (1, 4, hoje + timedelta(days=1), 1, 2, StatusConsulta.AGENDADA, StatusLembrete.ENVIADO, None),
        (1, 5, hoje + timedelta(days=2), 1, 1, StatusConsulta.AGENDADA, StatusLembrete.PENDENTE, None),
        (2, 6, hoje + timedelta(days=2), 1, 0, StatusConsulta.AGENDADA, StatusLembrete.PENDENTE, None),
        (2, 7, hoje + timedelta(days=4), 1, 1, StatusConsulta.AGENDADA, StatusLembrete.PENDENTE, None),
        (3, 8, hoje + timedelta(days=1), 1, 0, StatusConsulta.AGENDADA, StatusLembrete.ENVIADO, None),
        (3, 9, hoje + timedelta(days=3), 1, 3, StatusConsulta.AGENDADA, StatusLembrete.PENDENTE, None),
        (4, 11, hoje + timedelta(days=1), 1, 0, StatusConsulta.AGENDADA, StatusLembrete.PENDENTE, None),
        (4, 12, hoje + timedelta(days=2), 1, 1, StatusConsulta.AGENDADA, StatusLembrete.ENVIADO, None),
        (5, 10, hoje + timedelta(days=2), 1, 0, StatusConsulta.AGENDADA, StatusLembrete.PENDENTE, None),
        (6, 13, hoje + timedelta(days=3), 1, 2, StatusConsulta.AGENDADA, StatusLembrete.PENDENTE, None),
        (7, 14, hoje + timedelta(days=4), 1, 1, StatusConsulta.AGENDADA, StatusLembrete.PENDENTE, None),
        # Consultas futuras canceladas
        (0, 4, hoje + timedelta(days=5), 1, 3, StatusConsulta.CANCELADA, StatusLembrete.PENDENTE, "Paciente solicitou reagendamento por viagem"),
        (1, 6, hoje + timedelta(days=6), 1, 4, StatusConsulta.CANCELADA, StatusLembrete.ENVIADO, "Imprevisto pessoal informado pelo paciente"),
        (4, 13, hoje + timedelta(days=5), 1, 2, StatusConsulta.CANCELADA, StatusLembrete.PENDENTE, "Conflito de horário escolar"),
        # Consultas passadas (histórico)
        (0, 0, hoje - timedelta(days=1), -1, 0, StatusConsulta.AGENDADA, StatusLembrete.ENVIADO, None),
        (1, 1, hoje - timedelta(days=2), -1, 1, StatusConsulta.AGENDADA, StatusLembrete.ENVIADO, None),
        (2, 3, hoje - timedelta(days=3), -1, 0, StatusConsulta.AGENDADA, StatusLembrete.ENVIADO, None),
        (3, 8, hoje - timedelta(days=4), -1, 2, StatusConsulta.CANCELADA, StatusLembrete.ENVIADO, "Paciente não pôde comparecer"),
        (4, 11, hoje - timedelta(days=5), -1, 0, StatusConsulta.AGENDADA, StatusLembrete.ENVIADO, None),
        (5, 14, hoje - timedelta(days=7), -1, 1, StatusConsulta.AGENDADA, StatusLembrete.ENVIADO, None),
    ]

    criadas = 0
    ignoradas = 0
    horarios_ocupados_medico: set[Tuple[int, datetime]] = set()
    horarios_ocupados_paciente: set[Tuple[int, datetime]] = set()

    for idx_med, idx_pac, data_base, passo, slot_idx, status, lembrete, motivo in planos:
        medico = medicos_ativos[idx_med % len(medicos_ativos)]
        paciente = pacientes_ativos[idx_pac % len(pacientes_ativos)]
        medico_id = medico.getId()
        paciente_id = paciente.getId()
        if medico_id is None or paciente_id is None:
            continue

        data_hora = _proximo_slot_disponivel(medico, data_base, duracao, slot_idx, passo_dias=passo)
        if data_hora is None:
            continue

        # Evita conflito de horário no mesmo lote de seed
        if (medico_id, data_hora) in horarios_ocupados_medico or (paciente_id, data_hora) in horarios_ocupados_paciente:
            continue

        if _existe_consulta(medico_id, paciente_id, data_hora):
            ignoradas += 1
            horarios_ocupados_medico.add((medico_id, data_hora))
            horarios_ocupados_paciente.add((paciente_id, data_hora))
            continue

        if status == StatusConsulta.AGENDADA and (
            data_hora.time() in Consulta.listarHorariosOcupados(medico_id, data_hora.date())
            or Consulta.existeConflitoPaciente(paciente_id, data_hora)
        ):
            ignoradas += 1
            continue

        consulta = Consulta()
        consulta.setPaciente(paciente)
        consulta.setMedico(medico)
        consulta.setDataHora(data_hora)
        consulta.setStatus(status)
        consulta.setLembrete(lembrete)
        consulta.setMotivoCancelamento(motivo)
        consulta.salvar()

        horarios_ocupados_medico.add((medico_id, data_hora))
        horarios_ocupados_paciente.add((paciente_id, data_hora))
        criadas += 1

    return criadas, ignoradas


def popular_banco(reset: bool = False) -> None:
    """Inicializa o schema e popula o banco com dados fictícios."""
    inicializar_banco()

    if reset:
        _limpar_dados_existentes()

    agora = config.agora_clinica()

    u_criados, u_ign = _seed_usuarios()
    medicos, m_criados, m_ign = _seed_medicos()
    pacientes, p_criados, p_ign = _seed_pacientes()
    a_criadas, a_ign = _seed_ausencias(medicos, agora.date())
    c_criadas, c_ign = _seed_consultas(medicos, pacientes, agora)

    print("\n=== Resumo da população do banco ===")
    print(f"Usuários:  {u_criados} criados, {u_ign} já existentes")
    print(f"Médicos:   {m_criados} criados, {m_ign} já existentes")
    print(f"Pacientes: {p_criados} criados, {p_ign} já existentes")
    print(f"Ausências: {a_criadas} criadas, {a_ign} já existentes")
    print(f"Consultas: {c_criadas} criadas, {c_ign} já existentes")
    print("\nCredenciais disponíveis para login:")
    print("  - Administrador: admin / admin123")
    print("  - Administrador: coord.clinica / admin123")
    print("  - Recepcionistas: recepcao1, recepcao2, carla.recepcao, lucas.recepcao / recepcao123")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Popula o banco de dados Agenda Médica.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Limpa os registros atuais (exceto especialidades e admin) antes de popular.",
    )
    args = parser.parse_args()
    popular_banco(reset=args.reset)
