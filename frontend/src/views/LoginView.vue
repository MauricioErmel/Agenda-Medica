<script setup>
import { onMounted, ref } from 'vue'
import { AuthControllerApi } from '../services/api'

defineProps({
  clinicaNome: {
    type: String,
    default: 'Agenda Médica',
  },
})

const emit = defineEmits(['autenticado'])

const formularioVisivel = ref(false)
const login = ref('')
const senha = ref('')
const mostrarSenha = ref(false)
const carregando = ref(false)
const mensagemErro = ref('')
let usuarioAutenticado = null

// Métodos alinhados ao Diagrama de Classes (v1) e Diagrama de Sequência (UC1)
function abrirSistema() {
  exibirFormulario()
}

function exibirFormulario() {
  formularioVisivel.value = true
}

function exibirErro(mensagem) {
  mensagemErro.value = mensagem
}

function exibirMenu(perfil) {
  emit('autenticado', { perfil, usuario: usuarioAutenticado })
}

async function enviarCredenciais(loginInformado = login.value, senhaInformada = senha.value) {
  mensagemErro.value = ''
  carregando.value = true

  try {
    const { usuario, mensagem } = await AuthControllerApi.entrar(loginInformado, senhaInformada)
    if (usuario !== null) {
      usuarioAutenticado = usuario
      exibirMenu(usuario.perfil)
    } else {
      exibirErro(mensagem || 'Login ou senha inválidos')
      exibirFormulario()
    }
  } catch {
    exibirErro('Não foi possível conectar ao servidor. Verifique se o back-end está em execução.')
    exibirFormulario()
  } finally {
    carregando.value = false
  }
}

onMounted(() => {
  abrirSistema()
})

defineExpose({
  abrirSistema,
  exibirFormulario,
  enviarCredenciais,
  exibirErro,
  exibirMenu,
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-4 bg-base-200">
    <div v-if="formularioVisivel" class="card w-full max-w-md bg-base-100 shadow-xl border border-base-300">
      <div class="card-body p-8">
        <div class="flex flex-col items-center text-center mb-6">
          <div class="w-14 h-14 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mb-3">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <h1 class="text-2xl font-bold text-base-content">{{ clinicaNome }}</h1>
          <p class="text-sm text-base-content/65 mt-1">
            Informe seu login e senha para acessar o sistema
          </p>
        </div>

        <div v-if="mensagemErro" role="alert" class="alert alert-error alert-soft mb-4 text-sm">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{{ mensagemErro }}</span>
        </div>

        <form class="space-y-4" @submit.prevent="enviarCredenciais(login, senha)">
          <fieldset class="fieldset">
            <legend class="fieldset-legend text-sm font-medium">Login</legend>
            <input
              id="input-login"
              v-model="login"
              type="text"
              autocomplete="username"
              placeholder="Digite seu login"
              class="input input-bordered w-full"
              :disabled="carregando"
              required
            />
          </fieldset>

          <fieldset class="fieldset">
            <legend class="fieldset-legend text-sm font-medium">Senha</legend>
            <div class="join w-full">
              <input
                id="input-senha"
                v-model="senha"
                :type="mostrarSenha ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="Digite sua senha"
                class="input input-bordered join-item w-full"
                :disabled="carregando"
                required
              />
              <button
                type="button"
                class="btn btn-outline join-item border-base-300"
                :title="mostrarSenha ? 'Ocultar senha' : 'Mostrar senha'"
                @click="mostrarSenha = !mostrarSenha"
              >
                <svg v-if="!mostrarSenha" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
              </button>
            </div>
          </fieldset>

          <button type="submit" class="btn btn-primary w-full mt-2" :disabled="carregando">
            <span v-if="carregando" class="loading loading-spinner loading-sm"></span>
            <span>{{ carregando ? 'Entrando...' : 'Entrar' }}</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
