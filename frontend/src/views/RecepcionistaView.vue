<script setup>
import { computed, onMounted, ref } from 'vue'
import { RecepcionistaControllerApi } from '../services/api'

// Estados da tela
const modo = ref('lista') // 'lista' | 'cadastro' | 'edicao'
const recepcionistas = ref([])
const filtroBusca = ref('')
const carregandoLista = ref(false)
const salvando = ref(false)

// Campos do formulário (mantidos em caso de erro conforme CU2 e CU3)
const formId = ref(null)
const formNome = ref('')
const formLogin = ref('')
const formSenha = ref('')
const mostrarSenha = ref(false)

// Feedback visual
const mensagemTexto = ref('')
const mensagemTipo = ref('info') // 'success' | 'error' | 'info'

const recepcionistasFiltradas = computed(() => {
  const termo = filtroBusca.value.trim().toLowerCase()
  if (!termo) return recepcionistas.value
  return recepcionistas.value.filter(
    (rec) =>
      rec.nome.toLowerCase().includes(termo) ||
      rec.login.toLowerCase().includes(termo)
  )
})

function limparMensagem() {
  mensagemTexto.value = ''
}

// Métodos alinhados ao Diagrama de Classes (v1) e Diagramas de Sequência (CU2 e CU3)
function exibirMensagem(mensagem, tipo = 'info') {
  mensagemTexto.value = mensagem
  mensagemTipo.value = tipo
}

function exibirLista(lista) {
  recepcionistas.value = lista
  modo.value = 'lista'
}

function exibirFormulario(usuario = null) {
  mostrarSenha.value = false
  if (usuario === null) {
    formId.value = null
    formNome.value = ''
    formLogin.value = ''
    formSenha.value = ''
    modo.value = 'cadastro'
  } else {
    formId.value = usuario.id
    formNome.value = usuario.nome
    formLogin.value = usuario.login
    formSenha.value = ''
    modo.value = 'edicao'
  }
}

function acionarCadastroRecepcionista() {
  limparMensagem()
  exibirFormulario(null)
}

async function acionarEdicaoRecepcionista() {
  limparMensagem()
  await carregarLista()
}

// Auxiliar interno: recarrega a lista sem apagar a mensagem atual
async function carregarLista() {
  carregandoLista.value = true
  try {
    const res = await RecepcionistaControllerApi.listarRecepcionistas()
    if (res.ok) {
      exibirLista(res.lista)
    } else {
      exibirMensagem(res.mensagem, 'error')
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao listar recepcionistas.', 'error')
  } finally {
    carregandoLista.value = false
  }
}

function selecionarRecepcionista(usuario) {
  limparMensagem()
  exibirFormulario(usuario)
}

async function enviarCadastro(
  nome = formNome.value,
  login = formLogin.value,
  senha = formSenha.value
) {
  limparMensagem()
  salvando.value = true
  try {
    const res = await RecepcionistaControllerApi.cadastrarRecepcionista(nome, login, senha)
    if (res.ok) {
      exibirMensagem(res.mensagem, 'success')
      await carregarLista()
    } else {
      // Fluxos alternativos 3a e 3b: sinaliza erro mantendo os dados digitados
      exibirMensagem(res.mensagem, 'error')
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao cadastrar.', 'error')
  } finally {
    salvando.value = false
  }
}

async function enviarEdicao(
  id = formId.value,
  nome = formNome.value,
  novaSenha = formSenha.value
) {
  limparMensagem()
  salvando.value = true
  try {
    const res = await RecepcionistaControllerApi.editarRecepcionista(id, nome, novaSenha)
    if (res.ok) {
      exibirMensagem(res.mensagem, 'success')
      await carregarLista()
    } else {
      // Fluxo alternativo 5a: sinaliza erro mantendo os dados digitados
      exibirMensagem(res.mensagem, 'error')
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao salvar alterações.', 'error')
  } finally {
    salvando.value = false
  }
}

function cancelar() {
  formId.value = null
  formNome.value = ''
  formLogin.value = ''
  formSenha.value = ''
  limparMensagem()
  modo.value = 'lista'
}

function submeterFormulario() {
  if (modo.value === 'cadastro') {
    enviarCadastro(formNome.value, formLogin.value, formSenha.value)
  } else if (modo.value === 'edicao') {
    enviarEdicao(formId.value, formNome.value, formSenha.value)
  }
}

onMounted(() => {
  acionarEdicaoRecepcionista()
})

defineExpose({
  acionarCadastroRecepcionista,
  acionarEdicaoRecepcionista,
  selecionarRecepcionista,
  exibirLista,
  exibirFormulario,
  enviarCadastro,
  enviarEdicao,
  cancelar,
  exibirMensagem,
})
</script>

<template>
  <section class="space-y-6">
    <!-- Cabeçalho da seção -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-base-content">Gestão de Recepcionistas</h2>
        <p class="text-sm text-base-content/65">
          Cadastre novas colaboradoras e mantenha os dados de acesso da equipe atualizados.
        </p>
      </div>

      <div class="flex gap-2">
        <button
          v-if="modo !== 'lista'"
          type="button"
          class="btn btn-outline btn-sm sm:btn-md"
          @click="acionarEdicaoRecepcionista()"
        >
          Ver Lista
        </button>
        <button
          v-if="modo === 'lista'"
          type="button"
          class="btn btn-primary btn-sm sm:btn-md gap-2"
          @click="acionarCadastroRecepcionista()"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          Cadastrar Recepcionista
        </button>
      </div>
    </div>

    <!-- Alerta de feedback -->
    <div
      v-if="mensagemTexto"
      role="alert"
      class="alert alert-soft flex items-center justify-between"
      :class="{
        'alert-success': mensagemTipo === 'success',
        'alert-error': mensagemTipo === 'error',
        'alert-info': mensagemTipo === 'info',
      }"
    >
      <div class="flex items-center gap-2">
        <svg v-if="mensagemTipo === 'success'" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="font-medium">{{ mensagemTexto }}</span>
      </div>
      <button type="button" class="btn btn-ghost btn-xs" @click="limparMensagem()">Fechar</button>
    </div>

    <!-- Modo Lista (CU3 - passo 1 e 2) -->
    <div v-if="modo === 'lista'" class="card bg-base-100 shadow-sm border border-base-300">
      <div class="card-body p-6">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <h3 class="text-lg font-semibold">
            Recepcionistas Cadastradas
            <span class="badge badge-neutral badge-sm ml-2">{{ recepcionistas.length }}</span>
          </h3>

          <label class="input input-bordered input-sm flex items-center gap-2 w-full sm:w-72">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              v-model="filtroBusca"
              type="text"
              class="grow"
              placeholder="Filtrar por nome ou login..."
            />
          </label>
        </div>

        <div v-if="carregandoLista" class="flex justify-center py-10">
          <span class="loading loading-spinner loading-lg text-primary"></span>
        </div>

        <div v-else-if="recepcionistas.length === 0" class="text-center py-10 space-y-3">
          <p class="text-base-content/70">Nenhuma recepcionista cadastrada até o momento.</p>
          <button
            type="button"
            class="btn btn-primary btn-sm"
            @click="acionarCadastroRecepcionista()"
          >
            Cadastrar Primeira Recepcionista
          </button>
        </div>

        <div v-else-if="recepcionistasFiltradas.length === 0" class="text-center py-8 text-base-content/60">
          Nenhuma recepcionista encontrada para o filtro "{{ filtroBusca }}".
        </div>

        <div v-else class="overflow-x-auto">
          <table class="table table-zebra">
            <thead>
              <tr>
                <th>Nome Completo</th>
                <th>Login</th>
                <th class="text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recepcionistasFiltradas" :key="rec.id" class="hover:bg-base-200/60">
                <td class="font-medium">{{ rec.nome }}</td>
                <td>
                  <code class="px-2 py-0.5 rounded bg-base-200 text-sm">{{ rec.login }}</code>
                </td>
                <td class="text-right">
                  <button
                    type="button"
                    class="btn btn-outline btn-primary btn-sm gap-1.5"
                    @click="selecionarRecepcionista(rec)"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    Editar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Modo Formulário (CU2: Cadastro | CU3: Edição) -->
    <div v-else class="card bg-base-100 shadow-sm border border-base-300 max-w-2xl">
      <div class="card-body p-6 sm:p-8">
        <div class="mb-4">
          <h3 class="text-xl font-bold">
            {{ modo === 'cadastro' ? 'Cadastrar Nova Recepcionista' : 'Editar Recepcionista' }}
          </h3>
          <p class="text-sm text-base-content/65 mt-0.5">
            <template v-if="modo === 'cadastro'">
              Preencha todos os campos obrigatórios para criar o acesso da recepcionista.
            </template>
            <template v-else>
              Altere o nome completo e/ou informe uma nova senha. O login não pode ser alterado.
            </template>
          </p>
        </div>

        <form class="space-y-4" novalidate @submit.prevent="submeterFormulario()">
          <fieldset class="fieldset">
            <legend class="fieldset-legend text-sm font-medium">
              Nome Completo <span class="text-error">*</span>
            </legend>
            <input
              id="rec-nome"
              v-model="formNome"
              type="text"
              placeholder="Ex.: Maria Oliveira"
              class="input input-bordered w-full"
              :disabled="salvando"
            />
          </fieldset>

          <fieldset class="fieldset">
            <legend class="fieldset-legend text-sm font-medium">
              Login <span v-if="modo === 'cadastro'" class="text-error">*</span>
            </legend>
            <input
              id="rec-login"
              v-model="formLogin"
              type="text"
              placeholder="Ex.: maria.oliveira"
              class="input input-bordered w-full"
              :disabled="salvando || modo === 'edicao'"
              :readonly="modo === 'edicao'"
            />
            <p v-if="modo === 'cadastro'" class="label text-xs text-base-content/60">
              O login deve ser único entre todos os usuários do sistema (RN11).
            </p>
          </fieldset>

          <fieldset class="fieldset">
            <legend class="fieldset-legend text-sm font-medium">
              {{ modo === 'cadastro' ? 'Senha' : 'Nova Senha (opcional)' }}
              <span v-if="modo === 'cadastro'" class="text-error">*</span>
            </legend>
            <div class="join w-full">
              <input
                id="rec-senha"
                v-model="formSenha"
                :type="mostrarSenha ? 'text' : 'password'"
                :placeholder="
                  modo === 'cadastro'
                    ? 'Informe uma senha inicial'
                    : 'Deixe em branco para manter a senha atual'
                "
                class="input input-bordered join-item w-full"
                :disabled="salvando"
              />
              <button
                type="button"
                class="btn btn-outline join-item border-base-300"
                @click="mostrarSenha = !mostrarSenha"
              >
                {{ mostrarSenha ? 'Ocultar' : 'Mostrar' }}
              </button>
            </div>
          </fieldset>

          <div class="flex flex-wrap items-center justify-end gap-3 pt-4 border-t border-base-200">
            <button
              type="button"
              class="btn btn-ghost"
              :disabled="salvando"
              @click="cancelar()"
            >
              Cancelar
            </button>
            <button type="submit" class="btn btn-primary" :disabled="salvando">
              <span v-if="salvando" class="loading loading-spinner loading-sm"></span>
              <span>{{ modo === 'cadastro' ? 'Salvar Cadastro' : 'Salvar Alterações' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </section>
</template>
