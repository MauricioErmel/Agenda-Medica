<script setup>
import { onMounted, ref } from 'vue'
import AppNavbar from './components/AppNavbar.vue'
import AusenciaView from './views/AusenciaView.vue'
import ConsultaView from './views/ConsultaView.vue'
import LembreteView from './views/LembreteView.vue'
import LoginView from './views/LoginView.vue'
import MedicoView from './views/MedicoView.vue'
import PacienteView from './views/PacienteView.vue'
import RecepcionistaView from './views/RecepcionistaView.vue'
import { AuthControllerApi } from './services/api'

const usuarioAtual = ref(null)
const verificandoSessao = ref(true)
const clinicaNome = ref('Agenda Médica')
const abaAdmin = ref('recepcionistas') // 'recepcionistas' | 'medicos'
const abaRecepcionista = ref('pacientes') // 'pacientes' | 'consultas' | 'lembretes' | 'ausencias'

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
  abaAdmin.value = 'recepcionistas'
  abaRecepcionista.value = 'pacientes'
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

    <main class="container mx-auto max-w-5xl px-4 lg:px-8 py-8 flex-1 space-y-6">
      <!-- Menu do Perfil ADMINISTRADOR (UC2, UC3, UC4, UC5) -->
      <template v-if="usuarioAtual.perfil === 'ADMINISTRADOR'">
        <div role="tablist" class="tabs tabs-box bg-base-100 border border-base-300 w-fit p-1">
          <button
            type="button"
            role="tab"
            class="tab font-medium"
            :class="{ 'tab-active': abaAdmin === 'recepcionistas' }"
            @click="abaAdmin = 'recepcionistas'"
          >
            Recepcionistas
          </button>
          <button
            type="button"
            role="tab"
            class="tab font-medium"
            :class="{ 'tab-active': abaAdmin === 'medicos' }"
            @click="abaAdmin = 'medicos'"
          >
            Médicos
          </button>
        </div>

        <RecepcionistaView v-if="abaAdmin === 'recepcionistas'" />
        <MedicoView v-else />
      </template>

      <!-- Menu do Perfil RECEPCIONISTA (UC6 a UC11) -->
      <template v-else>
        <div role="tablist" class="tabs tabs-box bg-base-100 border border-base-300 w-fit p-1">
          <button
            type="button"
            role="tab"
            class="tab font-medium"
            :class="{ 'tab-active': abaRecepcionista === 'pacientes' }"
            @click="abaRecepcionista = 'pacientes'"
          >
            Pacientes
          </button>
          <button
            type="button"
            role="tab"
            class="tab font-medium"
            :class="{ 'tab-active': abaRecepcionista === 'consultas' }"
            @click="abaRecepcionista = 'consultas'"
          >
            Consultas
          </button>
          <button
            type="button"
            role="tab"
            class="tab font-medium"
            :class="{ 'tab-active': abaRecepcionista === 'lembretes' }"
            @click="abaRecepcionista = 'lembretes'"
          >
            Lembretes
          </button>
          <button
            type="button"
            role="tab"
            class="tab font-medium"
            :class="{ 'tab-active': abaRecepcionista === 'ausencias' }"
            @click="abaRecepcionista = 'ausencias'"
          >
            Ausências
          </button>
        </div>

        <PacienteView v-if="abaRecepcionista === 'pacientes'" />
        <ConsultaView v-else-if="abaRecepcionista === 'consultas'" />
        <LembreteView v-else-if="abaRecepcionista === 'lembretes'" />
        <AusenciaView v-else />
      </template>
    </main>
  </div>
</template>
