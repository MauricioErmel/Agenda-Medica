<script setup>
import { onMounted, ref } from 'vue'
import { LembreteControllerApi } from '../services/api'

// Etapas: 'lista' | 'confirmar_envio'
const etapa = ref('lista')
const consultas = ref([])
const consultaSelecionada = ref(null)
const urlWhatsAppAtual = ref('')
const carregando = ref(false)
const processando = ref(false)

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

function formatarDataHora(dataHoraIso) {
  if (!dataHoraIso) return '—'
  const [dataParte, horaParte] = String(dataHoraIso).split('T')
  const horaLimpa = horaParte ? horaParte.slice(0, 5) : ''
  return `${formatarData(dataParte)} às ${horaLimpa}`
}

// Auxiliar interno para recarregar a fila mantendo opcionalmente a mensagem de feedback
async function carregarLembretes(manterMensagem = false) {
  if (!manterMensagem) {
    limparMensagem()
  }
  consultaSelecionada.value = null
  urlWhatsAppAtual.value = ''
  etapa.value = 'lista'
  carregando.value = true
  try {
    const res = await LembreteControllerApi.listarLembretesPendentes()
    if (!res.ok) {
      consultas.value = []
      exibirMensagem(res.mensagem, 'erro')
      return
    }
    if (res.lista.length === 0) {
      consultas.value = []
      if (!manterMensagem) {
        exibirMensagem('Nenhuma consulta com lembrete pendente', 'aviso')
      }
    } else {
      exibirLembretesPendentes(res.lista)
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao carregar lembretes.', 'erro')
  } finally {
    carregando.value = false
  }
}

// Métodos alinhados ao Diagrama de Classes (v4) e Diagrama de Sequência (UC10)
function exibirMensagem(mensagem, tipo = 'info') {
  mensagemTexto.value = mensagem
  mensagemTipo.value = tipo
}

async function acionarLembretes() {
  await carregarLembretes(false)
}

function exibirLembretesPendentes(lista) {
  consultas.value = lista
  etapa.value = 'lista'
}

async function selecionarConsulta(consulta) {
  if (!consulta?.id) return
  limparMensagem()
  processando.value = true
  try {
    const res = await LembreteControllerApi.gerarLinkWhatsApp(consulta.id)
    if (!res.ok || !res.url) {
      exibirMensagem(res.mensagem || 'Consulta não elegível para lembrete', 'erro')
      return
    }
    abrirWhatsApp(res.url)
    solicitarConfirmacaoEnvio(consulta)
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao gerar link do WhatsApp.', 'erro')
  } finally {
    processando.value = false
  }
}

function abrirWhatsApp(url) {
  urlWhatsAppAtual.value = url
  if (typeof window !== 'undefined' && url) {
    window.open(url, '_blank', 'noopener,noreferrer')
  }
}

function solicitarConfirmacaoEnvio(consulta) {
  consultaSelecionada.value = consulta
  etapa.value = 'confirmar_envio'
}

async function confirmarEnvio(consultaId = consultaSelecionada.value?.id) {
  if (!consultaId) return
  limparMensagem()
  processando.value = true
  try {
    const res = await LembreteControllerApi.confirmarEnvio(consultaId)
    if (res.ok) {
      exibirMensagem(res.mensagem, 'sucesso')
      await carregarLembretes(true)
    } else {
      exibirMensagem(res.mensagem, 'erro')
      await carregarLembretes(true)
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao confirmar envio.', 'erro')
  } finally {
    processando.value = false
  }
}

async function cancelar() {
  // Extensão 5a: mantém o lembrete Pendente e retorna ao passo 1
  await carregarLembretes(false)
}

onMounted(() => {
  acionarLembretes()
})

defineExpose({
  acionarLembretes,
  exibirLembretesPendentes,
  selecionarConsulta,
  abrirWhatsApp,
  solicitarConfirmacaoEnvio,
  confirmarEnvio,
  cancelar,
  exibirMensagem,
})
</script>

<template>
  <section class="space-y-6">
    <!-- Cabeçalho -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-base-content">Lembretes via WhatsApp</h2>
        <p class="text-sm text-base-content/65">
          Envie lembretes para consultas futuras agendadas com lembrete pendente, em ordem cronológica.
        </p>
      </div>

      <button
        type="button"
        class="btn btn-outline btn-sm sm:btn-md"
        :disabled="carregando || processando"
        @click="acionarLembretes()"
      >
        <span v-if="carregando" class="loading loading-spinner loading-xs"></span>
        <span>Atualizar Lista</span>
      </button>
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

    <!-- Etapa 1: Lista de consultas futuras Agendadas com lembrete Pendente -->
    <div v-if="etapa === 'lista'" class="card bg-base-100 shadow-sm border border-base-300">
      <div class="card-body p-6 space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold">
            Consultas com Lembrete Pendente
            <span v-if="consultas.length > 0" class="badge badge-neutral badge-sm ml-1">
              {{ consultas.length }}
            </span>
          </h3>
        </div>

        <div v-if="carregando" class="flex justify-center py-8">
          <span class="loading loading-spinner loading-lg text-primary"></span>
        </div>

        <div v-else-if="consultas.length > 0" class="overflow-x-auto">
          <table class="table table-zebra">
            <thead>
              <tr>
                <th>Data e Hora</th>
                <th>Paciente</th>
                <th>Telefone</th>
                <th>Médico</th>
                <th>Lembrete</th>
                <th class="text-right">Ação</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="cons in consultas" :key="cons.id" class="hover:bg-base-200/60">
                <td class="font-medium whitespace-nowrap">{{ formatarDataHora(cons.dataHora) }}</td>
                <td>{{ cons.paciente?.nome || '—' }}</td>
                <td class="whitespace-nowrap">{{ cons.paciente?.telefone || '—' }}</td>
                <td>
                  <div>{{ cons.medico?.nome || '—' }}</div>
                  <div class="text-xs text-base-content/60">
                    {{ cons.medico?.especialidade?.nome || '' }}
                  </div>
                </td>
                <td>
                  <span class="badge badge-warning badge-soft badge-sm">Pendente</span>
                </td>
                <td class="text-right">
                  <button
                    type="button"
                    class="btn btn-primary btn-sm"
                    :disabled="processando"
                    @click="selecionarConsulta(cons)"
                  >
                    Enviar WhatsApp
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="text-center py-8 text-base-content/60 text-sm">
          Nenhuma consulta com lembrete pendente no momento.
        </div>
      </div>
    </div>

    <!-- Etapa 2: Confirmação após abertura do WhatsApp -->
    <div v-else-if="etapa === 'confirmar_envio'" class="card bg-base-100 shadow-sm border border-base-300 max-w-2xl">
      <div class="card-body p-6 sm:p-8 space-y-5">
        <div>
          <h3 class="text-xl font-bold">Confirmar Envio do Lembrete</h3>
          <p class="text-sm text-base-content/65 mt-0.5">
            O WhatsApp foi aberto com a mensagem padrão preenchida. Após enviar a mensagem ao paciente, confirme abaixo para marcar o lembrete como <strong>Enviado</strong>.
          </p>
        </div>

        <div class="rounded-xl bg-base-200/70 border border-base-300 p-4 space-y-1 text-sm">
          <div>
            <span class="text-base-content/65">Paciente:</span>
            <strong class="ml-1">{{ consultaSelecionada?.paciente?.nome }}</strong>
          </div>
          <div>
            <span class="text-base-content/65">Telefone:</span>
            <strong class="ml-1">{{ consultaSelecionada?.paciente?.telefone }}</strong>
          </div>
          <div>
            <span class="text-base-content/65">Médico:</span>
            <strong class="ml-1">{{ consultaSelecionada?.medico?.nome }}</strong>
            <span v-if="consultaSelecionada?.medico?.especialidade?.nome" class="text-base-content/65">
              ({{ consultaSelecionada?.medico?.especialidade?.nome }})
            </span>
          </div>
          <div>
            <span class="text-base-content/65">Data e Hora:</span>
            <strong class="ml-1">{{ formatarDataHora(consultaSelecionada?.dataHora) }}</strong>
          </div>
        </div>

        <div v-if="urlWhatsAppAtual" class="text-sm">
          <a
            :href="urlWhatsAppAtual"
            target="_blank"
            rel="noopener noreferrer"
            class="link link-primary font-medium"
          >
            Abrir WhatsApp novamente em nova aba
          </a>
        </div>

        <div class="flex flex-wrap items-center justify-end gap-3 pt-4 border-t border-base-200">
          <button
            type="button"
            class="btn btn-ghost"
            :disabled="processando"
            @click="cancelar()"
          >
            Não Enviei (Manter Pendente)
          </button>
          <button
            type="button"
            class="btn btn-primary"
            :disabled="processando"
            @click="confirmarEnvio()"
          >
            <span v-if="processando" class="loading loading-spinner loading-sm"></span>
            <span>Confirmar Envio</span>
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
