<script setup>
import { computed, onMounted, ref } from 'vue'
import { ConsultaControllerApi, PacienteControllerApi } from '../services/api'

// Fluxo atual: 'agendamento' (UC8) | 'cancelamento' (UC9)
const fluxo = ref('agendamento')
// Etapas: 'buscar_paciente' | 'selecionar_medico_data' | 'selecionar_consulta' | 'confirmar_cancelamento'
const etapa = ref('buscar_paciente')

// Busca e seleção de paciente
const termoBusca = ref('')
const buscaRealizada = ref(false)
const pacientes = ref([])
const pacienteSelecionado = ref(null)
const carregandoBusca = ref(false)

// Agendamento (UC8)
const medicosAtivos = ref([])
const medicoSelecionadoId = ref('')
const dataSelecionada = ref('')
const horariosLivres = ref([])
const horarioSelecionado = ref('')
const buscaHorariosRealizada = ref(false)
const carregandoMedicos = ref(false)
const carregandoHorarios = ref(false)
const salvando = ref(false)

// Cancelamento (UC9)
const consultasPaciente = ref([])
const consultaSelecionada = ref(null)
const motivoCancelamento = ref('')
const carregandoConsultas = ref(false)

// Feedback visual
const mensagemTexto = ref('')
const mensagemTipo = ref('info') // 'sucesso' | 'erro' | 'aviso' | 'info'

const medicoSelecionadoObj = computed(() =>
  medicosAtivos.value.find((m) => m.id === Number(medicoSelecionadoId.value)) || null
)

function limparMensagem() {
  mensagemTexto.value = ''
}

function formatarCpf(cpf) {
  const digitos = String(cpf || '').replace(/\D/g, '')
  if (digitos.length !== 11) return cpf || ''
  return `${digitos.slice(0, 3)}.${digitos.slice(3, 6)}.${digitos.slice(6, 9)}-${digitos.slice(9)}`
}

function formatarData(dataIso) {
  if (!dataIso) return '—'
  const partes = String(dataIso).split('-')
  if (partes.length !== 3) return dataIso
  return `${partes[2]}/${partes[1]}/${partes[0]}`
}

function formatarDataHora(dataHoraIso) {
  if (!dataHoraIso) return '—'
  const [dataParte, horaParte] = String(dataHoraIso).split('T')
  const horaLimpa = horaParte ? horaParte.slice(0, 5) : ''
  return `${formatarData(dataParte)} às ${horaLimpa}`
}

function rotuloSituacao(situacao) {
  return situacao === 'ATIVO' ? 'Ativo' : 'Inativo'
}

function resetarEstadoFluxo() {
  termoBusca.value = ''
  buscaRealizada.value = false
  pacientes.value = []
  pacienteSelecionado.value = null
  medicosAtivos.value = []
  medicoSelecionadoId.value = ''
  dataSelecionada.value = ''
  horariosLivres.value = []
  horarioSelecionado.value = ''
  buscaHorariosRealizada.value = false
  consultasPaciente.value = []
  consultaSelecionada.value = null
  motivoCancelamento.value = ''
  etapa.value = 'buscar_paciente'
}

// Métodos alinhados ao Diagrama de Classes (v3) e Diagramas de Sequência (UC8 e UC9)
function exibirMensagem(mensagem, tipo = 'info') {
  mensagemTexto.value = mensagem
  mensagemTipo.value = tipo
}

function acionarAgendamento() {
  limparMensagem()
  fluxo.value = 'agendamento'
  resetarEstadoFluxo()
}

function acionarCancelamento() {
  limparMensagem()
  fluxo.value = 'cancelamento'
  resetarEstadoFluxo()
}

async function buscarPacientes(termo = termoBusca.value) {
  limparMensagem()
  termoBusca.value = termo
  const termoLimpo = (termo || '').trim()
  if (!termoLimpo) {
    pacientes.value = []
    buscaRealizada.value = false
    exibirMensagem('Informe o CPF ou parte do nome do paciente.', 'aviso')
    return
  }

  carregandoBusca.value = true
  buscaRealizada.value = true
  try {
    const res = await PacienteControllerApi.consultarPacientes(termoLimpo)
    if (!res.ok) {
      pacientes.value = []
      exibirMensagem(res.mensagem, 'erro')
      return
    }
    if (res.lista.length === 0) {
      pacientes.value = []
      exibirMensagem('Paciente não localizado', 'aviso')
    } else {
      exibirPacientes(res.lista)
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao consultar pacientes.', 'erro')
  } finally {
    carregandoBusca.value = false
  }
}

function exibirPacientes(lista) {
  pacientes.value = lista
  etapa.value = 'buscar_paciente'
}

async function selecionarPaciente(paciente) {
  limparMensagem()
  if (fluxo.value === 'agendamento') {
    carregandoMedicos.value = true
    try {
      const erroPaciente = await ConsultaControllerApi.verificarPaciente(paciente.id)
      if (erroPaciente !== null) {
        exibirMensagem(erroPaciente, 'erro')
        return
      }
      pacienteSelecionado.value = paciente
      const resMed = await ConsultaControllerApi.listarMedicosAtivos()
      if (!resMed.ok) {
        exibirMensagem(resMed.mensagem, 'erro')
        return
      }
      exibirMedicos(resMed.lista)
    } catch {
      exibirMensagem('Erro de comunicação com o servidor ao verificar paciente.', 'erro')
    } finally {
      carregandoMedicos.value = false
    }
  } else {
    carregandoConsultas.value = true
    try {
      pacienteSelecionado.value = paciente
      const resCons = await ConsultaControllerApi.listarConsultasFuturasPaciente(paciente.id)
      if (!resCons.ok) {
        exibirMensagem(resCons.mensagem, 'erro')
        return
      }
      if (resCons.lista.length === 0) {
        consultasPaciente.value = []
        exibirMensagem('Nenhuma consulta para cancelar', 'aviso')
      } else {
        exibirConsultasPaciente(resCons.lista)
      }
    } catch {
      exibirMensagem('Erro de comunicação com o servidor ao listar consultas.', 'erro')
    } finally {
      carregandoConsultas.value = false
    }
  }
}

function exibirMedicos(lista) {
  medicosAtivos.value = lista
  medicoSelecionadoId.value = lista.length > 0 ? String(lista[0].id) : ''
  dataSelecionada.value = ''
  horariosLivres.value = []
  horarioSelecionado.value = ''
  buscaHorariosRealizada.value = false
  etapa.value = 'selecionar_medico_data'
}

async function selecionarMedicoData(
  medicoId = Number(medicoSelecionadoId.value),
  data = dataSelecionada.value
) {
  limparMensagem()
  horarioSelecionado.value = ''
  if (!medicoId || !data) {
    horariosLivres.value = []
    exibirMensagem('Selecione um médico Ativo e uma data para consultar os horários.', 'aviso')
    return
  }

  carregandoHorarios.value = true
  buscaHorariosRealizada.value = true
  try {
    const res = await ConsultaControllerApi.listarHorariosLivres(medicoId, data)
    if (!res.ok) {
      horariosLivres.value = []
      exibirMensagem(res.mensagem, 'erro')
      return
    }
    if (res.horarios.length === 0) {
      horariosLivres.value = []
      exibirMensagem('Nenhum horário disponível', 'aviso')
    } else {
      exibirHorariosLivres(res.horarios)
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao consultar horários livres.', 'erro')
  } finally {
    carregandoHorarios.value = false
  }
}

function exibirHorariosLivres(horarios) {
  horariosLivres.value = horarios
  horarioSelecionado.value = ''
}

async function confirmarAgendamento(
  pacienteId = pacienteSelecionado.value?.id,
  medicoId = Number(medicoSelecionadoId.value),
  dataHora = dataSelecionada.value && horarioSelecionado.value
    ? `${dataSelecionada.value}T${horarioSelecionado.value}`
    : ''
) {
  if (!pacienteId || !medicoId || !dataHora) {
    exibirMensagem('Selecione um horário livre antes de confirmar.', 'aviso')
    return
  }

  limparMensagem()
  salvando.value = true
  try {
    const res = await ConsultaControllerApi.agendarConsulta(pacienteId, medicoId, dataHora)
    if (res.ok) {
      resetarEstadoFluxo()
      exibirMensagem(res.mensagem, 'sucesso')
    } else {
      exibirMensagem(res.mensagem, 'erro')
      const dataParte = String(dataHora).split('T')[0]
      const resHorarios = await ConsultaControllerApi.listarHorariosLivres(medicoId, dataParte)
      if (resHorarios.ok) {
        exibirHorariosLivres(resHorarios.horarios)
      }
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao agendar consulta.', 'erro')
  } finally {
    salvando.value = false
  }
}

function exibirConsultasPaciente(lista) {
  consultasPaciente.value = lista
  consultaSelecionada.value = null
  motivoCancelamento.value = ''
  etapa.value = 'selecionar_consulta'
}

function selecionarConsulta(consulta) {
  limparMensagem()
  solicitarMotivoCancelamento(consulta)
}

function solicitarMotivoCancelamento(consulta) {
  consultaSelecionada.value = consulta
  motivoCancelamento.value = ''
  etapa.value = 'confirmar_cancelamento'
}

async function confirmarCancelamento(
  consultaId = consultaSelecionada.value?.id,
  motivo = motivoCancelamento.value
) {
  if (!consultaId) return

  limparMensagem()
  salvando.value = true
  try {
    const res = await ConsultaControllerApi.cancelarConsulta(consultaId, motivo)
    if (res.ok) {
      resetarEstadoFluxo()
      exibirMensagem(res.mensagem, 'sucesso')
    } else {
      exibirMensagem(res.mensagem, 'erro')
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao cancelar consulta.', 'erro')
  } finally {
    salvando.value = false
  }
}

function cancelar() {
  limparMensagem()
  resetarEstadoFluxo()
}

onMounted(() => {
  acionarAgendamento()
})

defineExpose({
  acionarAgendamento,
  acionarCancelamento,
  buscarPacientes,
  exibirPacientes,
  selecionarPaciente,
  exibirMedicos,
  selecionarMedicoData,
  exibirHorariosLivres,
  confirmarAgendamento,
  exibirConsultasPaciente,
  selecionarConsulta,
  solicitarMotivoCancelamento,
  confirmarCancelamento,
  cancelar,
  exibirMensagem,
})
</script>

<template>
  <section class="space-y-6">
    <!-- Cabeçalho e seletor de operação (UC8 | UC9) -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-base-content">Consultas</h2>
        <p class="text-sm text-base-content/65">
          Agende novas consultas em horários livres da grade médica ou cancele agendamentos futuros.
        </p>
      </div>

      <div class="join">
        <button
          type="button"
          class="btn btn-sm sm:btn-md join-item"
          :class="fluxo === 'agendamento' ? 'btn-primary' : 'btn-outline'"
          @click="acionarAgendamento()"
        >
          Agendar Consulta
        </button>
        <button
          type="button"
          class="btn btn-sm sm:btn-md join-item"
          :class="fluxo === 'cancelamento' ? 'btn-primary' : 'btn-outline'"
          @click="acionarCancelamento()"
        >
          Cancelar Consulta
        </button>
      </div>
    </div>

    <!-- Alerta de feedback -->
    <div
      v-if="mensagemTexto"
      role="alert"
      class="alert alert-soft flex items-center justify-between"
      :class="{
        'alert-success': mensagemTipo === 'sucesso',
        'alert-error': mensagemTipo === 'erro',
        'alert-warning': mensagemTipo === 'aviso',
        'alert-info': mensagemTipo === 'info',
      }"
    >
      <div class="flex items-center gap-2">
        <svg
          v-if="mensagemTipo === 'sucesso'"
          xmlns="http://www.w3.org/2000/svg"
          class="w-5 h-5 shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          class="w-5 h-5 shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="font-medium">{{ mensagemTexto }}</span>
      </div>
      <button type="button" class="btn btn-ghost btn-xs" @click="limparMensagem()">Fechar</button>
    </div>

    <!-- Etapa 1 (UC8 e UC9): Buscar e selecionar paciente -->
    <div v-if="etapa === 'buscar_paciente'" class="card bg-base-100 shadow-sm border border-base-300">
      <div class="card-body p-6 space-y-5">
        <div>
          <h3 class="text-lg font-semibold">
            {{ fluxo === 'agendamento' ? '1. Selecionar Paciente para Agendamento' : '1. Selecionar Paciente para Cancelamento' }}
          </h3>
          <p class="text-sm text-base-content/65">
            Informe o CPF ou parte do nome do paciente para localizar o cadastro.
          </p>
        </div>

        <form class="flex flex-col sm:flex-row gap-3" @submit.prevent="buscarPacientes(termoBusca)">
          <label class="input input-bordered flex items-center gap-2 flex-1">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              id="cons-pac-busca"
              v-model="termoBusca"
              type="text"
              class="grow"
              placeholder="Digite o CPF ou parte do nome do paciente..."
            />
          </label>
          <button type="submit" class="btn btn-primary" :disabled="carregandoBusca">
            <span v-if="carregandoBusca" class="loading loading-spinner loading-sm"></span>
            <span>Buscar</span>
          </button>
        </form>

        <div v-if="carregandoBusca || carregandoMedicos || carregandoConsultas" class="flex justify-center py-8">
          <span class="loading loading-spinner loading-lg text-primary"></span>
        </div>

        <div v-else-if="pacientes.length > 0" class="overflow-x-auto">
          <table class="table table-zebra">
            <thead>
              <tr>
                <th>Nome Completo</th>
                <th>Nascimento</th>
                <th>CPF</th>
                <th>Situação</th>
                <th class="text-right">Ação</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="pac in pacientes" :key="pac.id" class="hover:bg-base-200/60">
                <td class="font-medium">{{ pac.nome }}</td>
                <td>{{ formatarData(pac.dataNascimento) }}</td>
                <td>
                  <code class="px-2 py-0.5 rounded bg-base-200 text-sm">{{ formatarCpf(pac.cpf) }}</code>
                </td>
                <td>
                  <span
                    class="badge badge-sm"
                    :class="pac.situacao === 'ATIVO' ? 'badge-success badge-soft' : 'badge-ghost'"
                  >
                    {{ rotuloSituacao(pac.situacao) }}
                  </span>
                </td>
                <td class="text-right">
                  <button
                    type="button"
                    class="btn btn-outline btn-primary btn-sm"
                    @click="selecionarPaciente(pac)"
                  >
                    Selecionar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else-if="!buscaRealizada" class="text-center py-8 text-base-content/60 text-sm">
          Informe o CPF ou parte do nome do paciente acima para iniciar
          {{ fluxo === 'agendamento' ? 'o agendamento de consulta.' : 'o cancelamento de consulta.' }}
        </div>
      </div>
    </div>

    <!-- Etapa 2 (UC8): Selecionar médico Ativo, data e horário livre -->
    <div v-else-if="etapa === 'selecionar_medico_data'" class="card bg-base-100 shadow-sm border border-base-300">
      <div class="card-body p-6 space-y-6">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-base-200">
          <div>
            <h3 class="text-lg font-semibold">2. Escolher Médico, Data e Horário</h3>
            <p class="text-sm text-base-content/70 mt-0.5">
              Paciente selecionado: <strong>{{ pacienteSelecionado?.nome }}</strong>
              (CPF {{ formatarCpf(pacienteSelecionado?.cpf) }})
            </p>
          </div>
          <button type="button" class="btn btn-ghost btn-sm" :disabled="salvando" @click="cancelar()">
            Cancelar
          </button>
        </div>

        <div v-if="medicosAtivos.length === 0" class="text-center py-8 space-y-3">
          <p class="text-base-content/70">Não há médicos Ativos cadastrados no momento.</p>
          <button type="button" class="btn btn-outline btn-sm" @click="cancelar()">Voltar</button>
        </div>

        <template v-else>
          <form
            class="grid grid-cols-1 md:grid-cols-3 gap-4 items-end"
            @submit.prevent="selecionarMedicoData(Number(medicoSelecionadoId), dataSelecionada)"
          >
            <fieldset class="fieldset md:col-span-1">
              <legend class="fieldset-legend text-sm font-medium">
                Médico Ativo <span class="text-error">*</span>
              </legend>
              <select
                id="cons-medico"
                v-model="medicoSelecionadoId"
                class="select select-bordered w-full"
                :disabled="carregandoHorarios || salvando"
              >
                <option v-for="med in medicosAtivos" :key="med.id" :value="String(med.id)">
                  {{ med.nome }} — {{ med.especialidade?.nome || 'Sem especialidade' }}
                </option>
              </select>
            </fieldset>

            <fieldset class="fieldset md:col-span-1">
              <legend class="fieldset-legend text-sm font-medium">
                Data da Consulta <span class="text-error">*</span>
              </legend>
              <input
                id="cons-data"
                v-model="dataSelecionada"
                type="date"
                class="input input-bordered w-full"
                :disabled="carregandoHorarios || salvando"
              />
            </fieldset>

            <div class="pb-1">
              <button
                type="submit"
                class="btn btn-primary w-full"
                :disabled="carregandoHorarios || salvando"
              >
                <span v-if="carregandoHorarios" class="loading loading-spinner loading-sm"></span>
                <span>Consultar Horários Livres</span>
              </button>
            </div>
          </form>

          <!-- Horários livres -->
          <div v-if="carregandoHorarios" class="flex justify-center py-6">
            <span class="loading loading-spinner loading-lg text-primary"></span>
          </div>

          <div v-else-if="horariosLivres.length > 0" class="space-y-4 pt-2 border-t border-base-200">
            <div>
              <h4 class="text-sm font-semibold">
                Horários livres em {{ formatarData(dataSelecionada) }}
                <span class="badge badge-neutral badge-sm ml-1">{{ horariosLivres.length }}</span>
              </h4>
              <p class="text-xs text-base-content/60">
                Selecione um horário abaixo e confirme o agendamento.
              </p>
            </div>

            <div class="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-6 gap-2">
              <button
                v-for="hora in horariosLivres"
                :key="hora"
                type="button"
                class="btn btn-sm"
                :class="horarioSelecionado === hora ? 'btn-primary' : 'btn-outline'"
                :disabled="salvando"
                @click="horarioSelecionado = hora"
              >
                {{ hora }}
              </button>
            </div>

            <div
              v-if="horarioSelecionado"
              class="rounded-xl bg-base-200/70 border border-base-300 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div class="text-sm space-y-0.5">
                <div class="font-semibold">Resumo do Agendamento</div>
                <div>
                  <strong>{{ medicoSelecionadoObj?.nome }}</strong>
                  ({{ medicoSelecionadoObj?.especialidade?.nome }})
                </div>
                <div>
                  Data e hora: <strong>{{ formatarData(dataSelecionada) }} às {{ horarioSelecionado }}</strong>
                </div>
              </div>

              <div class="flex items-center gap-2">
                <button
                  type="button"
                  class="btn btn-ghost btn-sm"
                  :disabled="salvando"
                  @click="cancelar()"
                >
                  Desistir
                </button>
                <button
                  type="button"
                  class="btn btn-primary btn-sm"
                  :disabled="salvando"
                  @click="confirmarAgendamento()"
                >
                  <span v-if="salvando" class="loading loading-spinner loading-xs"></span>
                  <span>Confirmar Agendamento</span>
                </button>
              </div>
            </div>
          </div>

          <div
            v-else-if="buscaHorariosRealizada"
            class="text-center py-6 text-sm text-base-content/60"
          >
            Escolha outra data ou outro médico para consultar novos horários.
          </div>
        </template>
      </div>
    </div>

    <!-- Etapa 2 (UC9): Listar consultas futuras Agendadas do paciente -->
    <div v-else-if="etapa === 'selecionar_consulta'" class="card bg-base-100 shadow-sm border border-base-300">
      <div class="card-body p-6 space-y-5">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-base-200">
          <div>
            <h3 class="text-lg font-semibold">2. Selecionar Consulta para Cancelar</h3>
            <p class="text-sm text-base-content/70 mt-0.5">
              Paciente: <strong>{{ pacienteSelecionado?.nome }}</strong>
              (CPF {{ formatarCpf(pacienteSelecionado?.cpf) }})
            </p>
          </div>
          <button type="button" class="btn btn-ghost btn-sm" @click="cancelar()">
            Cancelar
          </button>
        </div>

        <div class="overflow-x-auto">
          <table class="table table-zebra">
            <thead>
              <tr>
                <th>Data e Hora</th>
                <th>Médico</th>
                <th>Especialidade</th>
                <th>Situação</th>
                <th class="text-right">Ação</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="cons in consultasPaciente" :key="cons.id" class="hover:bg-base-200/60">
                <td class="font-medium">{{ formatarDataHora(cons.dataHora) }}</td>
                <td>{{ cons.medico?.nome || '—' }}</td>
                <td>{{ cons.medico?.especialidade?.nome || '—' }}</td>
                <td>
                  <span class="badge badge-info badge-soft badge-sm">Agendada</span>
                </td>
                <td class="text-right">
                  <button
                    type="button"
                    class="btn btn-outline btn-error btn-sm"
                    @click="selecionarConsulta(cons)"
                  >
                    Cancelar Consulta
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Etapa 3 (UC9): Exibir dados da consulta, motivo opcional e confirmação -->
    <div v-else-if="etapa === 'confirmar_cancelamento'" class="card bg-base-100 shadow-sm border border-base-300 max-w-2xl">
      <div class="card-body p-6 sm:p-8 space-y-5">
        <div>
          <h3 class="text-xl font-bold">Confirmar Cancelamento</h3>
          <p class="text-sm text-base-content/65 mt-0.5">
            Confira os dados da consulta abaixo. O horário voltará a ficar livre após a confirmação.
          </p>
        </div>

        <div class="rounded-xl bg-base-200/70 border border-base-300 p-4 space-y-1 text-sm">
          <div>
            <span class="text-base-content/65">Paciente:</span>
            <strong class="ml-1">{{ pacienteSelecionado?.nome }}</strong>
          </div>
          <div>
            <span class="text-base-content/65">Médico:</span>
            <strong class="ml-1">{{ consultaSelecionada?.medico?.nome }}</strong>
          </div>
          <div>
            <span class="text-base-content/65">Especialidade:</span>
            <strong class="ml-1">{{ consultaSelecionada?.medico?.especialidade?.nome }}</strong>
          </div>
          <div>
            <span class="text-base-content/65">Data e Hora:</span>
            <strong class="ml-1">{{ formatarDataHora(consultaSelecionada?.dataHora) }}</strong>
          </div>
        </div>

        <fieldset class="fieldset">
          <legend class="fieldset-legend text-sm font-medium">
            Motivo do Cancelamento (opcional)
          </legend>
          <textarea
            id="cons-motivo"
            v-model="motivoCancelamento"
            rows="3"
            maxlength="500"
            class="textarea textarea-bordered w-full"
            placeholder="Ex.: Paciente solicitou remarcação..."
            :disabled="salvando"
          ></textarea>
        </fieldset>

        <div class="flex flex-wrap items-center justify-end gap-3 pt-4 border-t border-base-200">
          <button
            type="button"
            class="btn btn-ghost"
            :disabled="salvando"
            @click="cancelar()"
          >
            Desistir
          </button>
          <button
            type="button"
            class="btn btn-error"
            :disabled="salvando"
            @click="confirmarCancelamento()"
          >
            <span v-if="salvando" class="loading loading-spinner loading-sm"></span>
            <span>Confirmar Cancelamento</span>
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
