<script setup>
import { onMounted, ref } from 'vue'
import { AusenciaControllerApi, ConsultaControllerApi } from '../services/api'

// Etapas: 'selecionar_medico' | 'registrar_ausencia'
const etapa = ref('selecionar_medico')
const medicosAtivos = ref([])
const medicoSelecionado = ref(null)
const ausenciasFuturas = ref([])

// Formulário de nova ausência
const motivo = ref('')
const dataInicial = ref('')
const dataFinal = ref('')
const confirmandoRegistro = ref(false)

// Estados de carregamento
const carregandoMedicos = ref(false)
const carregandoAusencias = ref(false)
const validando = ref(false)
const salvando = ref(false)

// Feedback visual
const mensagemTexto = ref('')
const mensagemTipo = ref('info') // 'sucesso' | 'erro' | 'aviso' | 'info'

function limparMensagem() {
  mensagemTexto.value = ''
}

function formatarData(dataIso) {
  if (!dataIso) return '—'
  const partes = String(dataIso).split('-')
  if (partes.length !== 3) return dataIso
  return `${partes[2]}/${partes[1]}/${partes[0]}`
}

function limparFormulario() {
  motivo.value = ''
  dataInicial.value = ''
  dataFinal.value = ''
  confirmandoRegistro.value = false
}

// Auxiliar interno para recarregar ausências futuras do médico selecionado
async function recarregarAusenciasMedico(medicoId) {
  carregandoAusencias.value = true
  try {
    const res = await AusenciaControllerApi.listarAusenciasFuturas(medicoId)
    if (res.ok) {
      exibirAusenciasFuturas(res.lista)
    } else {
      ausenciasFuturas.value = []
      exibirMensagem(res.mensagem, 'erro')
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao carregar ausências.', 'erro')
  } finally {
    carregandoAusencias.value = false
  }
}

// Métodos alinhados ao Diagrama de Classes (v4) e Diagrama de Sequência (UC11)
function exibirMensagem(mensagem, tipo = 'info') {
  mensagemTexto.value = mensagem
  mensagemTipo.value = tipo
}

async function acionarRegistroAusencia() {
  limparMensagem()
  limparFormulario()
  medicoSelecionado.value = null
  ausenciasFuturas.value = []
  etapa.value = 'selecionar_medico'
  carregandoMedicos.value = true
  try {
    const res = await ConsultaControllerApi.listarMedicosAtivos()
    if (!res.ok) {
      medicosAtivos.value = []
      exibirMensagem(res.mensagem, 'erro')
      return
    }
    exibirMedicos(res.lista)
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao carregar médicos ativos.', 'erro')
  } finally {
    carregandoMedicos.value = false
  }
}

function exibirMedicos(lista) {
  medicosAtivos.value = lista
  etapa.value = 'selecionar_medico'
}

async function selecionarMedico(medico) {
  if (!medico?.id) return
  limparMensagem()
  limparFormulario()
  medicoSelecionado.value = medico
  etapa.value = 'registrar_ausencia'
  await recarregarAusenciasMedico(medico.id)
}

function exibirAusenciasFuturas(lista) {
  ausenciasFuturas.value = lista
}

async function enviarAusencia(
  medicoId = medicoSelecionado.value?.id,
  motivoTexto = motivo.value,
  dataIni = dataInicial.value,
  dataFim = dataFinal.value
) {
  if (!medicoId) return
  limparMensagem()
  validando.value = true
  try {
    const erro = await AusenciaControllerApi.validarAusencia(
      medicoId,
      motivoTexto,
      dataIni,
      dataFim
    )
    if (erro !== null) {
      exibirMensagem(erro, 'erro')
      return
    }
    solicitarConfirmacao()
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao validar ausência.', 'erro')
  } finally {
    validando.value = false
  }
}

function solicitarConfirmacao() {
  confirmandoRegistro.value = true
}

async function confirmarRegistro(
  medicoId = medicoSelecionado.value?.id,
  motivoTexto = motivo.value,
  dataIni = dataInicial.value,
  dataFim = dataFinal.value
) {
  if (!medicoId) return
  limparMensagem()
  salvando.value = true
  try {
    const res = await AusenciaControllerApi.registrarAusencia(
      medicoId,
      motivoTexto,
      dataIni,
      dataFim
    )
    if (res.ok) {
      limparFormulario()
      exibirMensagem(res.mensagem, 'sucesso')
      await recarregarAusenciasMedico(medicoId)
    } else {
      confirmandoRegistro.value = false
      exibirMensagem(res.mensagem, 'erro')
    }
  } catch {
    confirmandoRegistro.value = false
    exibirMensagem('Erro de comunicação com o servidor ao registrar ausência.', 'erro')
  } finally {
    salvando.value = false
  }
}

function cancelar() {
  acionarRegistroAusencia()
}

onMounted(() => {
  acionarRegistroAusencia()
})

defineExpose({
  acionarRegistroAusencia,
  exibirMedicos,
  selecionarMedico,
  exibirAusenciasFuturas,
  enviarAusencia,
  solicitarConfirmacao,
  confirmarRegistro,
  cancelar,
  exibirMensagem,
})
</script>

<template>
  <section class="space-y-6">
    <!-- Cabeçalho -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-base-content">Ausências Médicas</h2>
        <p class="text-sm text-base-content/65">
          Registre períodos de ausência (em dias inteiros) de médicos ativos para bloquear os horários na agenda.
        </p>
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

    <!-- Etapa 1: Listar médicos Ativos -->
    <div v-if="etapa === 'selecionar_medico'" class="card bg-base-100 shadow-sm border border-base-300">
      <div class="card-body p-6 space-y-4">
        <div>
          <h3 class="text-lg font-semibold">1. Selecionar Médico Ativo</h3>
          <p class="text-sm text-base-content/65">
            Escolha um médico ativo para consultar as ausências futuras e registrar um novo período.
          </p>
        </div>

        <div v-if="carregandoMedicos" class="flex justify-center py-8">
          <span class="loading loading-spinner loading-lg text-primary"></span>
        </div>

        <div v-else-if="medicosAtivos.length > 0" class="overflow-x-auto">
          <table class="table table-zebra">
            <thead>
              <tr>
                <th>Nome Completo</th>
                <th>CRM/UF</th>
                <th>Especialidade</th>
                <th class="text-right">Ação</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="med in medicosAtivos" :key="med.id" class="hover:bg-base-200/60">
                <td class="font-medium">{{ med.nome }}</td>
                <td>
                  <code class="px-2 py-0.5 rounded bg-base-200 text-sm">
                    {{ med.crm }}/{{ med.ufCrm }}
                  </code>
                </td>
                <td>{{ med.especialidade?.nome || '—' }}</td>
                <td class="text-right">
                  <button
                    type="button"
                    class="btn btn-outline btn-primary btn-sm"
                    @click="selecionarMedico(med)"
                  >
                    Selecionar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="text-center py-8 text-base-content/60 text-sm">
          Não há médicos ativos cadastrados no momento.
        </div>
      </div>
    </div>

    <!-- Etapa 2: Ausências futuras + Formulário de registro -->
    <div v-else-if="etapa === 'registrar_ausencia'" class="space-y-6">
      <div class="card bg-base-100 shadow-sm border border-base-300">
        <div class="card-body p-6 space-y-5">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-base-200">
            <div>
              <h3 class="text-lg font-semibold">
                2. Ausências de {{ medicoSelecionado?.nome }}
              </h3>
              <p class="text-sm text-base-content/70 mt-0.5">
                CRM {{ medicoSelecionado?.crm }}/{{ medicoSelecionado?.ufCrm }} —
                {{ medicoSelecionado?.especialidade?.nome }}
              </p>
            </div>
            <button
              type="button"
              class="btn btn-ghost btn-sm"
              :disabled="validando || salvando"
              @click="cancelar()"
            >
              Voltar / Cancelar
            </button>
          </div>

          <!-- Lista de ausências futuras já registradas -->
          <div class="space-y-2">
            <h4 class="text-sm font-semibold">
              Ausências futuras já registradas
              <span v-if="ausenciasFuturas.length > 0" class="badge badge-neutral badge-sm ml-1">
                {{ ausenciasFuturas.length }}
              </span>
            </h4>

            <div v-if="carregandoAusencias" class="flex justify-center py-4">
              <span class="loading loading-spinner loading-md text-primary"></span>
            </div>

            <div v-else-if="ausenciasFuturas.length > 0" class="overflow-x-auto">
              <table class="table table-sm table-zebra">
                <thead>
                  <tr>
                    <th>Data Inicial</th>
                    <th>Data Final</th>
                    <th>Motivo</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="aus in ausenciasFuturas" :key="aus.id">
                    <td class="whitespace-nowrap font-medium">{{ formatarData(aus.dataInicial) }}</td>
                    <td class="whitespace-nowrap font-medium">{{ formatarData(aus.dataFinal) }}</td>
                    <td>{{ aus.motivo }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <p v-else class="text-sm text-base-content/60">
              Nenhuma ausência futura registrada para este médico.
            </p>
          </div>

          <!-- Formulário de nova ausência -->
          <form
            class="space-y-4 pt-4 border-t border-base-200"
            @submit.prevent="enviarAusencia()"
          >
            <h4 class="text-base font-semibold">Registrar Nova Ausência</h4>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <fieldset class="fieldset">
                <legend class="fieldset-legend text-sm font-medium">
                  Data Inicial <span class="text-error">*</span>
                </legend>
                <input
                  id="aus-data-inicial"
                  v-model="dataInicial"
                  type="date"
                  class="input input-bordered w-full"
                  :disabled="validando || salvando || confirmandoRegistro"
                />
              </fieldset>

              <fieldset class="fieldset">
                <legend class="fieldset-legend text-sm font-medium">
                  Data Final <span class="text-error">*</span>
                </legend>
                <input
                  id="aus-data-final"
                  v-model="dataFinal"
                  type="date"
                  class="input input-bordered w-full"
                  :disabled="validando || salvando || confirmandoRegistro"
                />
              </fieldset>
            </div>

            <fieldset class="fieldset">
              <legend class="fieldset-legend text-sm font-medium">
                Motivo da Ausência <span class="text-error">*</span>
              </legend>
              <textarea
                id="aus-motivo"
                v-model="motivo"
                rows="3"
                maxlength="500"
                class="textarea textarea-bordered w-full"
                placeholder="Ex.: Congresso médico, férias, licença..."
                :disabled="validando || salvando || confirmandoRegistro"
              ></textarea>
            </fieldset>

            <!-- Bloco de confirmação antes de gravar -->
            <div
              v-if="confirmandoRegistro"
              class="rounded-xl bg-base-200/80 border border-primary/40 p-4 space-y-3"
            >
              <div class="text-sm space-y-1">
                <div class="font-semibold text-base-content">Confirmar Registro de Ausência</div>
                <p class="text-base-content/75">
                  Os horários de <strong>{{ medicoSelecionado?.nome }}</strong> entre
                  <strong>{{ formatarData(dataInicial) }}</strong> e
                  <strong>{{ formatarData(dataFinal) }}</strong> ficarão bloqueados para agendamento.
                </p>
                <p class="text-base-content/75">
                  Motivo: <strong>{{ motivo }}</strong>
                </p>
              </div>
              <div class="flex flex-wrap items-center justify-end gap-2">
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
                  @click="confirmarRegistro()"
                >
                  <span v-if="salvando" class="loading loading-spinner loading-xs"></span>
                  <span>Confirmar Registro</span>
                </button>
              </div>
            </div>

            <div v-else class="flex flex-wrap items-center justify-end gap-3 pt-2">
              <button
                type="button"
                class="btn btn-ghost"
                :disabled="validando || salvando"
                @click="cancelar()"
              >
                Cancelar
              </button>
              <button
                type="submit"
                class="btn btn-primary"
                :disabled="validando || salvando"
              >
                <span v-if="validando" class="loading loading-spinner loading-sm"></span>
                <span>Salvar Ausência</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </section>
</template>
