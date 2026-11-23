<script setup>
import { onMounted, ref } from 'vue'
import AppNavbar from './components/AppNavbar.vue'
import LoginView from './views/LoginView.vue'
import RecepcionistaView from './views/RecepcionistaView.vue'
import { AuthControllerApi } from './services/api'

const usuarioAtual = ref(null)
const verificandoSessao = ref(true)
const clinicaNome = ref('Agenda Médica')

async function carregarEstadoInicial() {
  try {
    const [infoClinica, usuarioSessao] = await Promise.all([
      AuthControllerApi.obterInfoClinica().catch(() => null),
      AuthControllerApi.verificarSessao().catch(() => null),
    ])
    if (infoClinica?.nome) {
      clinicaNome.value = infoClinica.nome
    }
    usuarioAtual.value = usuarioSessao
  } finally {
    verificandoSessao.value = false
  }
}

function aoAutenticar({ usuario }) {
  usuarioAtual.value = usuario
}

async function encerrarSessao() {
  await AuthControllerApi.sair()
  usuarioAtual.value = null
}

onMounted(() => {
  carregarEstadoInicial()
})
</script>

<template>
  <div v-if="verificandoSessao" class="min-h-screen flex items-center justify-center bg-base-200">
    <span class="loading loading-spinner loading-lg text-primary"></span>
  </div>

  <LoginView
    v-else-if="!usuarioAtual"
    :clinica-nome="clinicaNome"
    @autenticado="aoAutenticar"
  />

  <div v-else class="min-h-screen flex flex-col bg-base-200">
    <AppNavbar
      :usuario="usuarioAtual"
      :clinica-nome="clinicaNome"
      @sair="encerrarSessao"
    />

    <main class="container mx-auto max-w-5xl px-4 lg:px-8 py-8 flex-1">
      <!-- Menu do Perfil ADMINISTRADOR (CU2, CU3 ativos no Ciclo 1) -->
      <template v-if="usuarioAtual.perfil === 'ADMINISTRADOR'">
        <RecepcionistaView />
      </template>

      <!-- Menu do Perfil RECEPCIONISTA (Autenticação pronta no Ciclo 1; módulos nos Ciclos 2–4) -->
      <template v-else>
        <div class="card bg-base-100 shadow-sm border border-base-300">
          <div class="card-body p-8 space-y-5">
            <div>
              <span class="badge badge-secondary badge-soft mb-2">Área da Recepção</span>
              <h2 class="text-2xl font-bold text-base-content">
                Olá, {{ usuarioAtual.nome }}!
              </h2>
              <p class="text-base-content/70 mt-1">
                Você está autenticada como <strong>Recepcionista</strong>. As funcionalidades operacionais deste perfil serão liberadas nos próximos ciclos do desenvolvimento:
              </p>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div class="p-4 rounded-xl bg-base-200/70 border border-base-300">
                <div class="flex items-center justify-between mb-1">
                  <h3 class="font-semibold">Pacientes</h3>
                  <span class="badge badge-ghost badge-sm">Ciclo 2</span>
                </div>
                <p class="text-sm text-base-content/65">
                  Cadastro, consulta, edição e inativação de pacientes (CU6 e CU7).
                </p>
              </div>

              <div class="p-4 rounded-xl bg-base-200/70 border border-base-300">
                <div class="flex items-center justify-between mb-1">
                  <h3 class="font-semibold">Consultas</h3>
                  <span class="badge badge-ghost badge-sm">Ciclo 3</span>
                </div>
                <p class="text-sm text-base-content/65">
                  Agendamento sem conflitos e cancelamento de consultas (CU8 e CU9).
                </p>
              </div>

              <div class="p-4 rounded-xl bg-base-200/70 border border-base-300">
                <div class="flex items-center justify-between mb-1">
                  <h3 class="font-semibold">Lembretes WhatsApp</h3>
                  <span class="badge badge-ghost badge-sm">Ciclo 4</span>
                </div>
                <p class="text-sm text-base-content/65">
                  Envio de lembretes de consultas futuras via mensagem padrão (CU10).
                </p>
              </div>

              <div class="p-4 rounded-xl bg-base-200/70 border border-base-300">
                <div class="flex items-center justify-between mb-1">
                  <h3 class="font-semibold">Ausências Médicas</h3>
                  <span class="badge badge-ghost badge-sm">Ciclo 4</span>
                </div>
                <p class="text-sm text-base-content/65">
                  Registro de bloqueios de agenda em dias inteiros (CU11).
                </p>
              </div>
            </div>
          </div>
        </div>
      </template>
    </main>
  </div>
</template>
