<script setup>
import { computed, onMounted, ref } from 'vue'
import { MedicoControllerApi } from '../services/api'

const UFS = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
  'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
  'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
]

const DIAS_SEMANA = [
  { codigo: 'SEGUNDA', rotulo: 'Segunda-feira', sigla: 'Seg' },
  { codigo: 'TERCA', rotulo: 'Terça-feira', sigla: 'Ter' },
  { codigo: 'QUARTA', rotulo: 'Quarta-feira', sigla: 'Qua' },
  { codigo: 'QUINTA', rotulo: 'Quinta-feira', sigla: 'Qui' },
  { codigo: 'SEXTA', rotulo: 'Sexta-feira', sigla: 'Sex' },
  { codigo: 'SABADO', rotulo: 'Sábado', sigla: 'Sáb' },
  { codigo: 'DOMINGO', rotulo: 'Domingo', sigla: 'Dom' },
]

// Estados da tela
const modo = ref('lista') // 'lista' | 'cadastro' | 'edicao'
const medicos = ref([])
const especialidades = ref([])
const filtroBusca = ref('')
const carregandoLista = ref(false)
const carregandoFormulario = ref(false)
const salvando = ref(false)
const modalConfirmacaoAberto = ref(false)

// Campos do formulário (mantidos em caso de erro conforme CU4 e CU5)
const formId = ref(null)
const formNome = ref('')
const formCrm = ref('')
const formUfCrm = ref('RS')
const formEspecialidadeId = ref('')
const formSituacao = ref('ATIVO')
const formGrades = ref(criarGradesVazias())

// Feedback visual
const mensagemTexto = ref('')
const mensagemTipo = ref('info') // 'sucesso' | 'erro' | 'aviso' | 'info'

function criarGradesVazias() {
  return DIAS_SEMANA.map((dia) => ({
    diaSemana: dia.codigo,
    rotulo: dia.rotulo,
    ativo: false,
    horaInicial: '08:00',
    horaFinal: '12:00',
  }))
}

function extrairGradesSelecionadas() {
  return formGrades.value
    .filter((item) => item.ativo)
    .map((item) => ({
      diaSemana: item.diaSemana,
      horaInicial: item.horaInicial,
      horaFinal: item.horaFinal,
    }))
}

const medicosFiltrados = computed(() => {
  const termo = filtroBusca.value.trim().toLowerCase()
  if (!termo) return medicos.value
  return medicos.value.filter((med) => {
    const crmUf = `${med.crm}/${med.ufCrm}`.toLowerCase()
    const esp = (med.especialidade?.nome || '').toLowerCase()
    return (
      med.nome.toLowerCase().includes(termo) ||
      crmUf.includes(termo) ||
      esp.includes(termo)
    )
  })
})

function limparMensagem() {
  mensagemTexto.value = ''
}

function rotuloSituacao(situacao) {
  return situacao === 'ATIVO' ? 'Ativo' : 'Inativo'
}

function resumirGrades(grades) {
  if (!grades || grades.length === 0) return 'Sem grade'
  const mapaSigla = Object.fromEntries(DIAS_SEMANA.map((d) => [d.codigo, d.sigla]))
  return grades
    .map((g) => `${mapaSigla[g.diaSemana] || g.diaSemana} ${g.horaInicial}–${g.horaFinal}`)
    .join(' · ')
}

// Auxiliar interno: recarrega a lista sem apagar a mensagem atual
async function carregarLista() {
  carregandoLista.value = true
  try {
    const res = await MedicoControllerApi.listarMedicos()
    if (res.ok) {
      exibirLista(res.lista)
    } else {
      exibirMensagem(res.mensagem, 'erro')
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao listar médicos.', 'erro')
  } finally {
    carregandoLista.value = false
  }
}

// Métodos alinhados ao Diagrama de Classes (v2) e Diagramas de Sequência (CU4 e CU5)
function exibirMensagem(mensagem, tipo = 'info') {
  mensagemTexto.value = mensagem
  mensagemTipo.value = tipo
}

function exibirLista(lista) {
  medicos.value = lista
  modo.value = 'lista'
}

function exibirFormulario(medico = null, listaEspecialidades = []) {
  especialidades.value = listaEspecialidades
  modalConfirmacaoAberto.value = false
  const gradesBase = criarGradesVazias()

  if (medico === null) {
    formId.value = null
    formNome.value = ''
    formCrm.value = ''
    formUfCrm.value = 'RS'
    formEspecialidadeId.value = listaEspecialidades.length > 0 ? listaEspecialidades[0].id : ''
    formSituacao.value = 'ATIVO'
    formGrades.value = gradesBase
    modo.value = 'cadastro'
  } else {
    formId.value = medico.id
    formNome.value = medico.nome || ''
    formCrm.value = medico.crm || ''
    formUfCrm.value = medico.ufCrm || 'RS'
    formEspecialidadeId.value = medico.especialidade?.id || ''
    formSituacao.value = medico.situacao || 'ATIVO'

    const mapaGrades = new Map(
      (medico.grades || []).map((g) => [g.diaSemana, g])
    )
    formGrades.value = gradesBase.map((item) => {
      const existente = mapaGrades.get(item.diaSemana)
      if (existente) {
        return {
          ...item,
          ativo: true,
          horaInicial: existente.horaInicial || '08:00',
          horaFinal: existente.horaFinal || '12:00',
        }
      }
      return item
    })
    modo.value = 'edicao'
  }
}

async function acionarCadastroMedico() {
  limparMensagem()
  carregandoFormulario.value = true
  try {
    const resEsp = await MedicoControllerApi.listarEspecialidades()
    if (!resEsp.ok) {
      exibirMensagem(resEsp.mensagem, 'erro')
      return
    }
    exibirFormulario(null, resEsp.lista)
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao carregar especialidades.', 'erro')
  } finally {
    carregandoFormulario.value = false
  }
}

async function acionarEdicaoMedico() {
  limparMensagem()
  await carregarLista()
}

async function selecionarMedico(medico) {
  limparMensagem()
  carregandoFormulario.value = true
  try {
    const resMed = await MedicoControllerApi.buscarMedico(medico.id)
    if (!resMed.ok) {
      exibirMensagem(resMed.mensagem, 'erro')
      return
    }
    const resEsp = await MedicoControllerApi.listarEspecialidades()
    if (!resEsp.ok) {
      exibirMensagem(resEsp.mensagem, 'erro')
      return
    }
    exibirFormulario(resMed.medico, resEsp.lista)
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao carregar dados do médico.', 'erro')
  } finally {
    carregandoFormulario.value = false
  }
}

async function enviarCadastro(
  nome = formNome.value,
  crm = formCrm.value,
  ufCrm = formUfCrm.value,
  especialidadeId = Number(formEspecialidadeId.value),
  grades = extrairGradesSelecionadas()
) {
  limparMensagem()
  salvando.value = true
  try {
    const res = await MedicoControllerApi.cadastrarMedico(
      nome,
      crm,
      ufCrm,
      especialidadeId,
      grades
    )
    if (res.ok) {
      exibirMensagem(res.mensagem, 'sucesso')
      await carregarLista()
    } else {
      // Fluxos alternativos 3a e 3b: sinaliza erro mantendo dados
      exibirMensagem(res.mensagem, 'erro')
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao cadastrar médico.', 'erro')
  } finally {
    salvando.value = false
  }
}

async function enviarEdicao(
  id = formId.value,
  nome = formNome.value,
  crm = formCrm.value,
  ufCrm = formUfCrm.value,
  especialidadeId = Number(formEspecialidadeId.value),
  grades = extrairGradesSelecionadas(),
  situacao = formSituacao.value
) {
  limparMensagem()
  salvando.value = true
  try {
    const erroValidacao = await MedicoControllerApi.validarMedico(
      id,
      nome,
      crm,
      ufCrm,
      especialidadeId,
      grades,
      situacao
    )
    if (erroValidacao !== null) {
      exibirMensagem(erroValidacao, 'erro')
    } else {
      solicitarConfirmacao()
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao validar alterações.', 'erro')
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
  crm = formCrm.value,
  ufCrm = formUfCrm.value,
  especialidadeId = Number(formEspecialidadeId.value),
  grades = extrairGradesSelecionadas(),
  situacao = formSituacao.value
) {
  modalConfirmacaoAberto.value = false
  salvando.value = true
  try {
    const res = await MedicoControllerApi.editarMedico(
      id,
      nome,
      crm,
      ufCrm,
      especialidadeId,
      grades,
      situacao
    )
    if (res.ok) {
      exibirMensagem(res.mensagem, 'sucesso')
      await carregarLista()
    } else {
      exibirMensagem(res.mensagem, 'erro')
    }
  } catch {
    exibirMensagem('Erro de comunicação com o servidor ao atualizar médico.', 'erro')
  } finally {
    salvando.value = false
  }
}

function cancelar() {
  modalConfirmacaoAberto.value = false
  formId.value = null
  formNome.value = ''
  formCrm.value = ''
  formUfCrm.value = 'RS'
  formEspecialidadeId.value = ''
  formSituacao.value = 'ATIVO'
  formGrades.value = criarGradesVazias()
  limparMensagem()
  modo.value = 'lista'
}

function submeterFormulario() {
  const espId = Number(formEspecialidadeId.value)
  const grades = extrairGradesSelecionadas()
  if (modo.value === 'cadastro') {
    enviarCadastro(formNome.value, formCrm.value, formUfCrm.value, espId, grades)
  } else if (modo.value === 'edicao') {
    enviarEdicao(
      formId.value,
      formNome.value,
      formCrm.value,
      formUfCrm.value,
      espId,
      grades,
      formSituacao.value
    )
  }
}

onMounted(() => {
  acionarEdicaoMedico()
})

defineExpose({
  acionarCadastroMedico,
  acionarEdicaoMedico,
  exibirLista,
  selecionarMedico,
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
        <h2 class="text-2xl font-bold text-base-content">Gestão de Médicos</h2>
        <p class="text-sm text-base-content/65">
          Cadastre profissionais, defina especialidades e mantenha a grade semanal de atendimento.
        </p>
      </div>

      <div class="flex gap-2">
        <button
          v-if="modo !== 'lista'"
          type="button"
          class="btn btn-outline btn-sm sm:btn-md"
          @click="acionarEdicaoMedico()"
        >
          Ver Lista
        </button>
        <button
          v-if="modo === 'lista'"
          type="button"
          class="btn btn-primary btn-sm sm:btn-md gap-2"
          :disabled="carregandoFormulario"
          @click="acionarCadastroMedico()"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          Cadastrar Médico
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

    <!-- Modo Lista (CU5 - passos 1 e 2) -->
    <div v-if="modo === 'lista'" class="card bg-base-100 shadow-sm border border-base-300">
      <div class="card-body p-6">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <h3 class="text-lg font-semibold">
            Médicos Cadastrados
            <span class="badge badge-neutral badge-sm ml-2">{{ medicos.length }}</span>
          </h3>

          <label class="input input-bordered input-sm flex items-center gap-2 w-full sm:w-80">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              v-model="filtroBusca"
              type="text"
              class="grow"
              placeholder="Filtrar por nome, CRM ou especialidade..."
            />
          </label>
        </div>

        <div v-if="carregandoLista" class="flex justify-center py-10">
          <span class="loading loading-spinner loading-lg text-primary"></span>
        </div>

        <div v-else-if="medicos.length === 0" class="text-center py-10 space-y-3">
          <p class="text-base-content/70">Nenhum médico cadastrado até o momento.</p>
          <button
            type="button"
            class="btn btn-primary btn-sm"
            @click="acionarCadastroMedico()"
          >
            Cadastrar Primeiro Médico
          </button>
        </div>

        <div v-else-if="medicosFiltrados.length === 0" class="text-center py-8 text-base-content/60">
          Nenhum médico encontrado para o filtro "{{ filtroBusca }}".
        </div>

        <div v-else class="overflow-x-auto">
          <table class="table table-zebra">
            <thead>
              <tr>
                <th>Nome Completo</th>
                <th>CRM / UF</th>
                <th>Especialidade</th>
                <th>Situação</th>
                <th class="text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="med in medicosFiltrados" :key="med.id" class="hover:bg-base-200/60">
                <td>
                  <div class="font-medium">{{ med.nome }}</div>
                  <div class="text-xs text-base-content/60 mt-0.5">{{ resumirGrades(med.grades) }}</div>
                </td>
                <td>
                  <code class="px-2 py-0.5 rounded bg-base-200 text-sm">{{ med.crm }}/{{ med.ufCrm }}</code>
                </td>
                <td>{{ med.especialidade?.nome || '—' }}</td>
                <td>
                  <span
                    class="badge badge-sm"
                    :class="med.situacao === 'ATIVO' ? 'badge-success badge-soft' : 'badge-ghost'"
                  >
                    {{ rotuloSituacao(med.situacao) }}
                  </span>
                </td>
                <td class="text-right">
                  <button
                    type="button"
                    class="btn btn-outline btn-primary btn-sm gap-1.5"
                    :disabled="carregandoFormulario"
                    @click="selecionarMedico(med)"
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

    <!-- Modo Formulário (CU4: Cadastro | CU5: Edição) -->
    <div v-else class="card bg-base-100 shadow-sm border border-base-300">
      <div class="card-body p-6 sm:p-8">
        <div class="mb-4">
          <h3 class="text-xl font-bold">
            {{ modo === 'cadastro' ? 'Cadastrar Novo Médico' : 'Editar Médico' }}
          </h3>
          <p class="text-sm text-base-content/65 mt-0.5">
            <template v-if="modo === 'cadastro'">
              Informe os dados do profissional, especialidade e ao menos um dia na grade de atendimento.
            </template>
            <template v-else>
              Altere os dados desejados, grade de atendimento ou situação. Será solicitada confirmação antes de gravar.
            </template>
          </p>
        </div>

        <form class="space-y-5" novalidate @submit.prevent="submeterFormulario()">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <fieldset class="fieldset md:col-span-2">
              <legend class="fieldset-legend text-sm font-medium">
                Nome Completo <span class="text-error">*</span>
              </legend>
              <input
                id="med-nome"
                v-model="formNome"
                type="text"
                placeholder="Ex.: Dr. Carlos Eduardo Mendes"
                class="input input-bordered w-full"
                :disabled="salvando"
              />
            </fieldset>

            <fieldset class="fieldset">
              <legend class="fieldset-legend text-sm font-medium">
                CRM <span class="text-error">*</span>
              </legend>
              <input
                id="med-crm"
                v-model="formCrm"
                type="text"
                placeholder="Ex.: 123456"
                class="input input-bordered w-full"
                :disabled="salvando"
              />
            </fieldset>

            <fieldset class="fieldset">
              <legend class="fieldset-legend text-sm font-medium">
                UF do CRM <span class="text-error">*</span>
              </legend>
              <select
                id="med-uf"
                v-model="formUfCrm"
                class="select select-bordered w-full"
                :disabled="salvando"
              >
                <option v-for="uf in UFS" :key="uf" :value="uf">{{ uf }}</option>
              </select>
            </fieldset>

            <fieldset class="fieldset">
              <legend class="fieldset-legend text-sm font-medium">
                Especialidade <span class="text-error">*</span>
              </legend>
              <select
                id="med-especialidade"
                v-model="formEspecialidadeId"
                class="select select-bordered w-full"
                :disabled="salvando"
              >
                <option disabled value="">Selecione uma especialidade</option>
                <option v-for="esp in especialidades" :key="esp.id" :value="esp.id">
                  {{ esp.nome }}
                </option>
              </select>
            </fieldset>

            <fieldset v-if="modo === 'edicao'" class="fieldset">
              <legend class="fieldset-legend text-sm font-medium">
                Situação <span class="text-error">*</span>
              </legend>
              <select
                id="med-situacao"
                v-model="formSituacao"
                class="select select-bordered w-full"
                :disabled="salvando"
              >
                <option value="ATIVO">Ativo</option>
                <option value="INATIVO">Inativo</option>
              </select>
            </fieldset>
          </div>

          <!-- Grade de Atendimento -->
          <div class="space-y-3 pt-2">
            <div>
              <h4 class="text-sm font-semibold text-base-content">
                Grade de Atendimento <span class="text-error">*</span>
              </h4>
              <p class="text-xs text-base-content/60">
                Selecione ao menos um dia da semana e informe a hora inicial e final do turno (hora final maior que a inicial).
              </p>
            </div>

            <div class="border border-base-300 rounded-xl divide-y divide-base-200 overflow-hidden">
              <div
                v-for="item in formGrades"
                :key="item.diaSemana"
                class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-4 py-3"
                :class="item.ativo ? 'bg-base-100' : 'bg-base-200/40'"
              >
                <label class="flex items-center gap-3 cursor-pointer min-w-44">
                  <input
                    v-model="item.ativo"
                    type="checkbox"
                    class="checkbox checkbox-primary checkbox-sm"
                    :disabled="salvando"
                  />
                  <span class="text-sm font-medium" :class="{ 'text-base-content/50': !item.ativo }">
                    {{ item.rotulo }}
                  </span>
                </label>

                <div class="flex items-center gap-2 sm:gap-3">
                  <label class="flex items-center gap-1.5 text-xs text-base-content/70">
                    <span>Início</span>
                    <input
                      v-model="item.horaInicial"
                      type="time"
                      class="input input-bordered input-sm w-32"
                      :disabled="salvando || !item.ativo"
                    />
                  </label>
                  <span class="text-base-content/40">até</span>
                  <label class="flex items-center gap-1.5 text-xs text-base-content/70">
                    <span>Fim</span>
                    <input
                      v-model="item.horaFinal"
                      type="time"
                      class="input input-bordered input-sm w-32"
                      :disabled="salvando || !item.ativo"
                    />
                  </label>
                </div>
              </div>
            </div>
          </div>

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

    <!-- Modal de Confirmação da Edição (CU5 - passos 6 e 7) -->
    <dialog class="modal" :class="{ 'modal-open': modalConfirmacaoAberto }">
      <div class="modal-box">
        <h3 class="text-lg font-bold">Confirmar alteração do médico</h3>
        <p class="py-4 text-sm text-base-content/80">
          Deseja confirmar a gravação das alterações para <strong>{{ formNome }}</strong>
          ({{ formCrm }}/{{ formUfCrm }}, situação <strong>{{ rotuloSituacao(formSituacao) }}</strong>)?
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
