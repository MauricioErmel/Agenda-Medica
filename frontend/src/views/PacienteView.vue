<script setup>
import { onMounted, ref } from 'vue'
import { PacienteControllerApi } from '../services/api'

// Estados da tela
const modo = ref('consulta') // 'consulta' | 'cadastro' | 'edicao'
const termoBusca = ref('')
const buscaRealizada = ref(false)
const pacientes = ref([])
const carregandoBusca = ref(false)
const salvando = ref(false)
const modalConfirmacaoAberto = ref(false)

// Campos do formulário (mantidos em caso de erro conforme CU6 e CU7)
const formId = ref(null)
const formCpf = ref('')
const formNome = ref('')
const formDataNascimento = ref('')
const formSexo = ref('FEMININO')
const formTelefone = ref('')
const formSituacao = ref('ATIVO')

// Feedback visual
const mensagemTexto = ref('')
const mensagemTipo = ref('info') // 'sucesso' | 'erro' | 'aviso' | 'info'

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

function rotuloSituacao(situacao) {
  return situacao === 'ATIVO' ? 'Ativo' : 'Inativo'
}

// Auxiliar interno: atualiza resultado da consulta após edição mantendo a mensagem atual
async function atualizarConsultaAtual() {
  modo.value = 'consulta'
  if (!termoBusca.value.trim()) {
    pacientes.value = []
    return
  }
  try {
    const res = await PacienteControllerApi.consultarPacientes(termoBusca.value)
    if (res.ok) {
      pacientes.value = res.lista
    }
  } catch {
    // Mantém a mensagem de sucesso da edição já exibida
  }
}

// Métodos alinhados ao Diagrama de Classes (v2) e Diagramas de Sequência (CU6 e CU7)
function exibirMensagem(mensagem, tipo = 'info') {
  mensagemTexto.value = mensagem
  mensagemTipo.value = tipo
}

function acionarCadastroPaciente() {
  limparMensagem()
  exibirFormulario(null)
}

function acionarConsultaPaciente() {
  limparMensagem()
  modalConfirmacaoAberto.value = false
  modo.value = 'consulta'
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
      exibirLista(res.lista)
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao consultar pacientes.', 'erro')
  } finally {
    carregandoBusca.value = false
  }
}

function exibirLista(lista) {
  pacientes.value = lista
  modo.value = 'consulta'
}

function selecionarPaciente(paciente) {
  limparMensagem()
  exibirFormulario(paciente)
}

function exibirFormulario(paciente = null) {
  modalConfirmacaoAberto.value = false
  if (paciente === null) {
    formId.value = null
    formCpf.value = ''
    formNome.value = ''
    formDataNascimento.value = ''
    formSexo.value = 'FEMININO'
    formTelefone.value = ''
    formSituacao.value = 'ATIVO'
    modo.value = 'cadastro'
  } else {
    formId.value = paciente.id
    formCpf.value = formatarCpf(paciente.cpf)
    formNome.value = paciente.nome || ''
    formDataNascimento.value = paciente.dataNascimento || ''
    formSexo.value = paciente.sexo || 'FEMININO'
    formTelefone.value = paciente.telefone || ''
    formSituacao.value = paciente.situacao || 'ATIVO'
    modo.value = 'edicao'
  }
}

async function enviarCadastro(
  cpf = formCpf.value,
  nome = formNome.value,
  dataNascimento = formDataNascimento.value,
  sexo = formSexo.value,
  telefone = formTelefone.value
) {
  limparMensagem()
  salvando.value = true
  try {
    const res = await PacienteControllerApi.cadastrarPaciente(
      cpf,
      nome,
      dataNascimento,
      sexo,
      telefone
    )
    if (res.ok) {
      exibirMensagem(res.mensagem, 'sucesso')
      modo.value = 'consulta'
    } else {
      // Fluxos alternativos 3a e 3b (incluindo CPF duplicado): mantém dados no formulário
      exibirMensagem(res.mensagem, 'erro')
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao cadastrar paciente.', 'erro')
  } finally {
    salvando.value = false
  }
}

async function enviarEdicao(
  id = formId.value,
  nome = formNome.value,
  dataNascimento = formDataNascimento.value,
  sexo = formSexo.value,
  telefone = formTelefone.value,
  situacao = formSituacao.value
) {
  limparMensagem()
  salvando.value = true
  try {
    const erroValidacao = await PacienteControllerApi.validarPaciente(
      id,
      nome,
      dataNascimento,
      sexo,
      telefone,
      situacao
    )
    if (erroValidacao !== null) {
      exibirMensagem(erroValidacao, 'erro')
    } else {
      solicitarConfirmacao()
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao validar paciente.', 'erro')
  } finally {
    salvando.value = false
  }
}

function solicitarConfirmacao() {
  modalConfirmacaoAberto.value = true
}

async function confirmarEdicao(
  id = formId.value,
  nome = formNome.value,
  dataNascimento = formDataNascimento.value,
  sexo = formSexo.value,
  telefone = formTelefone.value,
  situacao = formSituacao.value
) {
  modalConfirmacaoAberto.value = false
  salvando.value = true
  try {
    const res = await PacienteControllerApi.editarPaciente(
      id,
      nome,
      dataNascimento,
      sexo,
      telefone,
      situacao
    )
    if (res.ok) {
      exibirMensagem(res.mensagem, 'sucesso')
      await atualizarConsultaAtual()
    } else {
      exibirMensagem(res.mensagem, 'erro')
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao atualizar paciente.', 'erro')
  } finally {
    salvando.value = false
  }
}

function cancelar() {
  modalConfirmacaoAberto.value = false
  formId.value = null
  formCpf.value = ''
  formNome.value = ''
  formDataNascimento.value = ''
  formSexo.value = 'FEMININO'
  formTelefone.value = ''
  formSituacao.value = 'ATIVO'
  limparMensagem()
  modo.value = 'consulta'
}

function submeterFormulario() {
  if (modo.value === 'cadastro') {
    enviarCadastro(
      formCpf.value,
      formNome.value,
      formDataNascimento.value,
      formSexo.value,
      formTelefone.value
    )
  } else if (modo.value === 'edicao') {
    enviarEdicao(
      formId.value,
      formNome.value,
      formDataNascimento.value,
      formSexo.value,
      formTelefone.value,
      formSituacao.value
    )
  }
}

onMounted(() => {
  acionarConsultaPaciente()
})

defineExpose({
  acionarCadastroPaciente,
  acionarConsultaPaciente,
  buscarPacientes,
  exibirLista,
  selecionarPaciente,
  exibirFormulario,
  enviarCadastro,
  enviarEdicao,
  solicitarConfirmacao,
  confirmarEdicao,
  cancelar,
  exibirMensagem,
})
</script>

<template>
  <section class="space-y-6">
    <!-- Cabeçalho da seção -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-base-content">Gestão de Pacientes</h2>
        <p class="text-sm text-base-content/65">
          Cadastre novos pacientes, consulte cadastros por CPF ou nome e mantenha dados e situação atualizados.
        </p>
      </div>

      <div class="flex gap-2">
        <button
          v-if="modo !== 'consulta'"
          type="button"
          class="btn btn-outline btn-sm sm:btn-md"
          @click="acionarConsultaPaciente()"
        >
          Consultar Pacientes
        </button>
        <button
          v-if="modo === 'consulta'"
          type="button"
          class="btn btn-primary btn-sm sm:btn-md gap-2"
          @click="acionarCadastroPaciente()"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          Cadastrar Paciente
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
        <svg v-if="mensagemTipo === 'sucesso'" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="font-medium">{{ mensagemTexto }}</span>
      </div>
      <button type="button" class="btn btn-ghost btn-xs" @click="limparMensagem()">Fechar</button>
    </div>

    <!-- Modo Consulta (CU7 - passos 1 a 3) -->
    <div v-if="modo === 'consulta'" class="card bg-base-100 shadow-sm border border-base-300">
      <div class="card-body p-6 space-y-5">
        <form class="flex flex-col sm:flex-row gap-3" @submit.prevent="buscarPacientes(termoBusca)">
          <label class="input input-bordered flex items-center gap-2 flex-1">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              id="pac-busca"
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

        <div v-if="carregandoBusca" class="flex justify-center py-8">
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
                <th class="text-right">Ações</th>
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
                    class="btn btn-outline btn-primary btn-sm gap-1.5"
                    @click="selecionarPaciente(pac)"
                  >
                    Consultar / Editar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else-if="!buscaRealizada" class="text-center py-8 text-base-content/60 text-sm">
          Informe o CPF ou parte do nome acima para consultar um paciente cadastrado, ou clique em
          <strong>Cadastrar Paciente</strong> para registrar um novo.
        </div>
      </div>
    </div>

    <!-- Modo Formulário (CU6: Cadastro | CU7: Consulta e Edição) -->
    <div v-else class="card bg-base-100 shadow-sm border border-base-300 max-w-2xl">
      <div class="card-body p-6 sm:p-8">
        <div class="mb-4">
          <h3 class="text-xl font-bold">
            {{ modo === 'cadastro' ? 'Cadastrar Novo Paciente' : 'Dados do Paciente' }}
          </h3>
          <p class="text-sm text-base-content/65 mt-0.5">
            <template v-if="modo === 'cadastro'">
              Preencha todos os dados obrigatórios. O paciente será cadastrado como Ativo.
            </template>
            <template v-else>
              O CPF não pode ser alterado (RN01). Altere os dados desejados ou a situação e clique em salvar.
            </template>
          </p>
        </div>

        <form class="space-y-4" novalidate @submit.prevent="submeterFormulario()">
          <fieldset class="fieldset">
            <legend class="fieldset-legend text-sm font-medium">
              CPF <span v-if="modo === 'cadastro'" class="text-error">*</span>
            </legend>
            <input
              id="pac-cpf"
              v-model="formCpf"
              type="text"
              placeholder="000.000.000-00"
              class="input input-bordered w-full"
              :disabled="salvando || modo === 'edicao'"
              :readonly="modo === 'edicao'"
            />
            <p v-if="modo === 'cadastro'" class="label text-xs text-base-content/60">
              Informe 11 dígitos numéricos. Deve ser único no sistema (RN01).
            </p>
          </fieldset>

          <fieldset class="fieldset">
            <legend class="fieldset-legend text-sm font-medium">
              Nome Completo <span class="text-error">*</span>
            </legend>
            <input
              id="pac-nome"
              v-model="formNome"
              type="text"
              placeholder="Ex.: João da Silva"
              class="input input-bordered w-full"
              :disabled="salvando"
            />
          </fieldset>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <fieldset class="fieldset">
              <legend class="fieldset-legend text-sm font-medium">
                Data de Nascimento <span class="text-error">*</span>
              </legend>
              <input
                id="pac-nascimento"
                v-model="formDataNascimento"
                type="date"
                class="input input-bordered w-full"
                :disabled="salvando"
              />
            </fieldset>

            <fieldset class="fieldset">
              <legend class="fieldset-legend text-sm font-medium">
                Sexo <span class="text-error">*</span>
              </legend>
              <select
                id="pac-sexo"
                v-model="formSexo"
                class="select select-bordered w-full"
                :disabled="salvando"
              >
                <option value="FEMININO">Feminino</option>
                <option value="MASCULINO">Masculino</option>
                <option value="OUTRO">Outro</option>
              </select>
            </fieldset>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <fieldset class="fieldset">
              <legend class="fieldset-legend text-sm font-medium">
                Telefone <span class="text-error">*</span>
              </legend>
              <input
                id="pac-telefone"
                v-model="formTelefone"
                type="tel"
                placeholder="Ex.: (51) 99999-8888"
                class="input input-bordered w-full"
                :disabled="salvando"
              />
            </fieldset>

            <fieldset v-if="modo === 'edicao'" class="fieldset">
              <legend class="fieldset-legend text-sm font-medium">
                Situação <span class="text-error">*</span>
              </legend>
              <select
                id="pac-situacao"
                v-model="formSituacao"
                class="select select-bordered w-full"
                :disabled="salvando"
              >
                <option value="ATIVO">Ativo</option>
                <option value="INATIVO">Inativo</option>
              </select>
            </fieldset>
          </div>

          <div class="flex flex-wrap items-center justify-end gap-3 pt-4 border-t border-base-200">
            <button
              type="button"
              class="btn btn-ghost"
              :disabled="salvando"
              @click="cancelar()"
            >
              {{ modo === 'edicao' ? 'Voltar / Cancelar' : 'Cancelar' }}
            </button>
            <button type="submit" class="btn btn-primary" :disabled="salvando">
              <span v-if="salvando" class="loading loading-spinner loading-sm"></span>
              <span>{{ modo === 'cadastro' ? 'Salvar Cadastro' : 'Salvar Alterações' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal de Confirmação da Edição (CU7 - passos 7 e 8) -->
    <dialog class="modal" :class="{ 'modal-open': modalConfirmacaoAberto }">
      <div class="modal-box">
        <h3 class="text-lg font-bold">Confirmar alteração do paciente</h3>
        <p class="py-4 text-sm text-base-content/80">
          Deseja confirmar a gravação das alterações para <strong>{{ formNome }}</strong>
          (CPF {{ formCpf }}, situação <strong>{{ rotuloSituacao(formSituacao) }}</strong>)?
        </p>
        <div class="modal-action">
          <button type="button" class="btn btn-ghost" :disabled="salvando" @click="cancelar()">
            Cancelar
          </button>
          <button
            type="button"
            class="btn btn-primary"
            :disabled="salvando"
            @click="confirmarEdicao()"
          >
            Confirmar Alterações
          </button>
        </div>
      </div>
    </dialog>
  </section>
</template>
