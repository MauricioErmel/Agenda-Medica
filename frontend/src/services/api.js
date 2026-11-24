const TOKEN_STORAGE_KEY = 'agenda_medica_token'

export function obterToken() {
  return sessionStorage.getItem(TOKEN_STORAGE_KEY)
}

export function salvarToken(token) {
  sessionStorage.setItem(TOKEN_STORAGE_KEY, token)
}

export function limparToken() {
  sessionStorage.removeItem(TOKEN_STORAGE_KEY)
}

async function requisitar(caminho, opcoes = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(opcoes.headers || {}),
  }

  const token = obterToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const resposta = await fetch(caminho, {
    ...opcoes,
    headers,
  })

  let dados = {}
  try {
    dados = await resposta.json()
  } catch {
    dados = {}
  }

  return {
    ok: resposta.ok,
    status: resposta.status,
    dados,
  }
}

export const AuthControllerApi = {
  async entrar(login, senha) {
    const res = await requisitar('/api/auth/entrar', {
      method: 'POST',
      body: JSON.stringify({ login, senha }),
    })
    if (res.ok && res.dados.token) {
      salvarToken(res.dados.token)
      return { usuario: res.dados.usuario, mensagem: null }
    }
    return {
      usuario: null,
      mensagem: res.dados.mensagem || 'Login ou senha inválidos',
    }
  },

  async verificarSessao() {
    if (!obterToken()) return null
    const res = await requisitar('/api/auth/sessao', { method: 'GET' })
    if (res.ok && res.dados.usuario) {
      return res.dados.usuario
    }
    limparToken()
    return null
  },

  async sair() {
    try {
      await requisitar('/api/auth/sair', { method: 'POST' })
    } finally {
      limparToken()
    }
  },

  async obterInfoClinica() {
    const res = await requisitar('/api/health', { method: 'GET' })
    return res.ok ? res.dados.clinica : null
  },
}

export const RecepcionistaControllerApi = {
  async listarRecepcionistas() {
    const res = await requisitar('/api/recepcionistas', { method: 'GET' })
    if (res.ok) {
      return { ok: true, lista: res.dados.recepcionistas || [], mensagem: null }
    }
    return {
      ok: false,
      lista: [],
      mensagem: res.dados.mensagem || 'Não foi possível carregar as recepcionistas.',
    }
  },

  async cadastrarRecepcionista(nome, login, senha) {
    const res = await requisitar('/api/recepcionistas', {
      method: 'POST',
      body: JSON.stringify({ nome, login, senha }),
    })
    return {
      ok: res.ok,
      mensagem: res.dados.mensagem || 'Erro ao cadastrar recepcionista.',
    }
  },

  async editarRecepcionista(id, nome, novaSenha) {
    const res = await requisitar(`/api/recepcionistas/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ nome, novaSenha }),
    })
    return {
      ok: res.ok,
      mensagem: res.dados.mensagem || 'Erro ao atualizar recepcionista.',
    }
  },
}

export const MedicoControllerApi = {
  async listarEspecialidades() {
    const res = await requisitar('/api/especialidades', { method: 'GET' })
    if (res.ok) {
      return { ok: true, lista: res.dados.especialidades || [], mensagem: null }
    }
    return {
      ok: false,
      lista: [],
      mensagem: res.dados.mensagem || 'Não foi possível carregar as especialidades.',
    }
  },

  async listarMedicos() {
    const res = await requisitar('/api/medicos', { method: 'GET' })
    if (res.ok) {
      return { ok: true, lista: res.dados.medicos || [], mensagem: null }
    }
    return {
      ok: false,
      lista: [],
      mensagem: res.dados.mensagem || 'Não foi possível carregar os médicos.',
    }
  },

  async buscarMedico(id) {
    const res = await requisitar(`/api/medicos/${id}`, { method: 'GET' })
    if (res.ok && res.dados.medico) {
      return { ok: true, medico: res.dados.medico, mensagem: null }
    }
    return {
      ok: false,
      medico: null,
      mensagem: res.dados.mensagem || 'Não foi possível carregar os dados do médico.',
    }
  },

  async cadastrarMedico(nome, crm, ufCrm, especialidadeId, grades) {
    const res = await requisitar('/api/medicos', {
      method: 'POST',
      body: JSON.stringify({ nome, crm, ufCrm, especialidadeId, grades }),
    })
    return {
      ok: res.ok,
      mensagem: res.dados.mensagem || 'Erro ao cadastrar médico.',
    }
  },

  async validarMedico(id, nome, crm, ufCrm, especialidadeId, grades, situacao) {
    const res = await requisitar(`/api/medicos/${id}/validar`, {
      method: 'POST',
      body: JSON.stringify({ nome, crm, ufCrm, especialidadeId, grades, situacao }),
    })
    if (res.ok && res.dados.valido) {
      return null
    }
    return res.dados.mensagem || 'Dados inválidos ou grade incoerente'
  },

  async editarMedico(id, nome, crm, ufCrm, especialidadeId, grades, situacao) {
    const res = await requisitar(`/api/medicos/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ nome, crm, ufCrm, especialidadeId, grades, situacao }),
    })
    return {
      ok: res.ok,
      mensagem: res.dados.mensagem || 'Erro ao atualizar médico.',
    }
  },
}

export const PacienteControllerApi = {
  async cadastrarPaciente(cpf, nome, dataNascimento, sexo, telefone) {
    const res = await requisitar('/api/pacientes', {
      method: 'POST',
      body: JSON.stringify({ cpf, nome, dataNascimento, sexo, telefone }),
    })
    return {
      ok: res.ok,
      mensagem: res.dados.mensagem || 'Erro ao cadastrar paciente.',
    }
  },

  async consultarPacientes(termo) {
    const query = encodeURIComponent(termo || '')
    const res = await requisitar(`/api/pacientes?termo=${query}`, { method: 'GET' })
    if (res.ok) {
      return { ok: true, lista: res.dados.pacientes || [], mensagem: null }
    }
    return {
      ok: false,
      lista: [],
      mensagem: res.dados.mensagem || 'Não foi possível consultar pacientes.',
    }
  },

  async validarPaciente(id, nome, dataNascimento, sexo, telefone, situacao) {
    const res = await requisitar(`/api/pacientes/${id}/validar`, {
      method: 'POST',
      body: JSON.stringify({ nome, dataNascimento, sexo, telefone, situacao }),
    })
    if (res.ok && res.dados.valido) {
      return null
    }
    return res.dados.mensagem || 'Dados inválidos'
  },

  async editarPaciente(id, nome, dataNascimento, sexo, telefone, situacao) {
    const res = await requisitar(`/api/pacientes/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ nome, dataNascimento, sexo, telefone, situacao }),
    })
    return {
      ok: res.ok,
      mensagem: res.dados.mensagem || 'Erro ao atualizar paciente.',
    }
  },
}

export const ConsultaControllerApi = {
  async verificarPaciente(pacienteId) {
    const res = await requisitar(`/api/consultas/pacientes/${pacienteId}/verificar`, {
      method: 'GET',
    })
    if (res.ok && res.dados.ativo) {
      return null
    }
    return res.dados.mensagem || 'Pacientes inativos não podem ser agendados'
  },

  async listarMedicosAtivos() {
    const res = await requisitar('/api/consultas/medicos-ativos', { method: 'GET' })
    if (res.ok) {
      return { ok: true, lista: res.dados.medicos || [], mensagem: null }
    }
    return {
      ok: false,
      lista: [],
      mensagem: res.dados.mensagem || 'Não foi possível carregar os médicos ativos.',
    }
  },

  async listarHorariosLivres(medicoId, data) {
    const query = new URLSearchParams({
      medicoId: String(medicoId || ''),
      data: String(data || ''),
    })
    const res = await requisitar(`/api/consultas/horarios-livres?${query.toString()}`, {
      method: 'GET',
    })
    if (res.ok) {
      return { ok: true, horarios: res.dados.horarios || [], mensagem: null }
    }
    return {
      ok: false,
      horarios: [],
      mensagem: res.dados.mensagem || 'Não foi possível consultar os horários livres.',
    }
  },

  async agendarConsulta(pacienteId, medicoId, dataHora) {
    const res = await requisitar('/api/consultas', {
      method: 'POST',
      body: JSON.stringify({ pacienteId, medicoId, dataHora }),
    })
    return {
      ok: res.ok,
      mensagem: res.dados.mensagem || 'Erro ao agendar consulta.',
    }
  },

  async listarConsultasFuturasPaciente(pacienteId) {
    const res = await requisitar(`/api/consultas/paciente/${pacienteId}/futuras`, {
      method: 'GET',
    })
    if (res.ok) {
      return { ok: true, lista: res.dados.consultas || [], mensagem: null }
    }
    return {
      ok: false,
      lista: [],
      mensagem: res.dados.mensagem || 'Não foi possível listar as consultas do paciente.',
    }
  },

  async cancelarConsulta(consultaId, motivo = '') {
    const res = await requisitar(`/api/consultas/${consultaId}/cancelar`, {
      method: 'PUT',
      body: JSON.stringify({ motivo }),
    })
    return {
      ok: res.ok,
      mensagem: res.dados.mensagem || 'Erro ao cancelar consulta.',
    }
  },
}

export const LembreteControllerApi = {
  async listarLembretesPendentes() {
    const res = await requisitar('/api/lembretes/pendentes', { method: 'GET' })
    if (res.ok) {
      return { ok: true, lista: res.dados.consultas || [], mensagem: null }
    }
    return {
      ok: false,
      lista: [],
      mensagem: res.dados.mensagem || 'Não foi possível carregar os lembretes pendentes.',
    }
  },

  async gerarLinkWhatsApp(consultaId) {
    const res = await requisitar(`/api/lembretes/${consultaId}/link-whatsapp`, {
      method: 'GET',
    })
    if (res.ok && res.dados.url) {
      return { ok: true, url: res.dados.url, mensagem: null }
    }
    return {
      ok: false,
      url: null,
      mensagem: res.dados.mensagem || 'Consulta não elegível para lembrete',
    }
  },

  async confirmarEnvio(consultaId) {
    const res = await requisitar(`/api/lembretes/${consultaId}/confirmar`, {
      method: 'PUT',
    })
    return {
      ok: res.ok,
      mensagem: res.dados.mensagem || 'Erro ao confirmar envio do lembrete.',
    }
  },
}

export const AusenciaControllerApi = {
  async listarAusenciasFuturas(medicoId) {
    const res = await requisitar(`/api/ausencias/medico/${medicoId}/futuras`, {
      method: 'GET',
    })
    if (res.ok) {
      return { ok: true, lista: res.dados.ausencias || [], mensagem: null }
    }
    return {
      ok: false,
      lista: [],
      mensagem: res.dados.mensagem || 'Não foi possível carregar as ausências futuras.',
    }
  },

  async validarAusencia(medicoId, motivo, dataInicial, dataFinal) {
    const res = await requisitar('/api/ausencias/validar', {
      method: 'POST',
      body: JSON.stringify({ medicoId, motivo, dataInicial, dataFinal }),
    })
    if (res.ok && res.dados.valido) {
      return null
    }
    return res.dados.mensagem || 'Dados inválidos para registro de ausência'
  },

  async registrarAusencia(medicoId, motivo, dataInicial, dataFinal) {
    const res = await requisitar('/api/ausencias', {
      method: 'POST',
      body: JSON.stringify({ medicoId, motivo, dataInicial, dataFinal }),
    })
    return {
      ok: res.ok,
      mensagem: res.dados.mensagem || 'Erro ao registrar ausência.',
    }
  },
}
