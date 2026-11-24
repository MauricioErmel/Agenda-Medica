# Logs do Desenvolvimento — Controle de Consultas

Este documento acompanha os ciclos iterativos (estilo Sprint) de modelagem UML (Diagrama de Classes e Diagramas de Sequência) e implementação do sistema **Agenda Médica**.

---

## Visão Geral dos Ciclos

O desenvolvimento foi dividido em **4 Ciclos**, agrupando os 11 casos de uso por dependência funcional:

| Ciclo | Foco | Casos de Uso |
|---|---|---|
| **Ciclo 1** | Autenticação e Gestão de Recepcionistas | UC1, UC2, UC3 |
| **Ciclo 2** | Cadastros Base (Médicos e Pacientes) | UC4, UC5, UC6, UC7 |
| **Ciclo 3** | Núcleo de Agendamento e Cancelamento | UC8, UC9 |
| **Ciclo 4** | Lembretes via WhatsApp e Ausências Médicas | UC10, UC11 |

---

## Ciclo 1: Autenticação e Gestão de Recepcionistas (UC1, UC2, UC3)

**Objetivo:** Estruturar a base do projeto e entregar o login de usuários (Administrador e Recepcionista) além do cadastro/edição de recepcionistas.

- [x] **1. Definir escopo do ciclo:** UC1 (Entrar no Sistema), UC2 (Cadastrar Recepcionista), UC3 (Editar Recepcionista).
- [x] **2. Diagrama de Classes (v1):** Modelar as classes iniciais com base no `Levantamento_de_Requisitos.md`.
- [x] **3. Diagramas de Sequência:** Criar os diagramas de sequência para UC1, UC2 e UC3.
- [x] **4. Revisar e ajustar Diagrama de Classes:** Refinar atributos, métodos e relacionamentos após análise dos diagramas de sequência.
- [x] **5. Desenvolver o código:** Implementar autenticação e CRUD de recepcionistas.
- [x] **6. Preparar incremento:** Consolidar o Diagrama de Classes para receber o Ciclo 2.

### Notas do Ciclo 1
- Gerado [diagrama_classes_v1.puml](diagramas/classes/diagrama_classes_v1.puml) no padrão MVC enxuto com getters e setters explícitos.
- Gerados os diagramas de sequência UML do Ciclo 1: [uc1_entrar_no_sistema.puml](diagramas/sequencia/uc1_entrar_no_sistema.puml), [uc2_cadastrar_recepcionista.puml](diagramas/sequencia/uc2_cadastrar_recepcionista.puml) e [uc3_editar_recepcionista.puml](diagramas/sequencia/uc3_editar_recepcionista.puml).
- Revisado e ajustado [diagrama_classes_v1.puml](diagramas/classes/diagrama_classes_v1.puml) para alinhar métodos de entrada/cancelamento nas Views, construtor explícito em `Usuario` e dependências `View ..> Usuario`.
- Passo 4 revisado contra os diagramas de sequência (associações, métodos, atributos, responsabilidades, classes e multiplicidade): removido `getSenha()` de `Usuario` (a senha só é usada dentro de `autenticar()` e `salvar()`) e incluída a dependência `RecepcionistaController ..> Perfil` (usa `Perfil.RECEPCIONISTA` no UC2). Demais critérios sem ajustes.
- Passo 5 concluído: implementado schema MySQL (`database/schema.sql`), back-end MVC em Python puro (`backend/model`, `backend/controller`, `backend/server.py`, `backend/init_db.py`) e front-end Vue 3 + Tailwind CSS + DaisyUI tema `autumn` (`frontend/`). Validado com 14 testes unitários/API e teste ponta a ponta (UC1, UC2 e UC3) no `MySQL80` real.
- Passo 6 concluído: código auditado contra os diagramas de classes e de sequência (visibilidade, assinaturas, estáticos, navegabilidade, multiplicidade, `<<create>>`, ordem das chamadas, `alt`/`opt` e retornos). Ajustes:
  - Código: `LoginView.exibirMenu(perfil)` passou a ter a assinatura do diagrama; o parâmetro extra `manterMensagem` de `acionarEdicaoRecepcionista()` virou o auxiliar interno `carregarLista()`.
  - Diagramas: `exibirMensagem(mensagem, tipo)` em `RecepcionistaView` (classes, UC2 e UC3), `to_dict()` em `Usuario` e nota sobre a infraestrutura não modelada (API HTTP, `Database` e auxiliares internos).
  - Mantidas sem modelar, por serem validações defensivas: `AuthController.entrar()` recusa login/senha vazios sem consultar o banco, e `editarRecepcionista()` recusa id inexistente ou de Administrador.
  - 14 testes do back-end passando. O `frontend/dist` precisa ser gerado de novo (`npm install` e `npm run build`) para refletir os ajustes do front-end.
- Próximo passo: iniciar o Ciclo 2 (UC4 a UC7).

---

## Ciclo 2: Cadastros Base — Médicos e Pacientes (UC4, UC5, UC6, UC7)

**Objetivo:** Permitir o cadastro, consulta e edição de médicos (com especialidade única e grade de atendimento) e pacientes.

- [x] **1. Definir escopo do ciclo:** UC4 (Cadastrar Médico), UC5 (Editar Médico), UC6 (Cadastrar Paciente), UC7 (Consultar e Editar Paciente).
- [x] **2. Incrementar Diagrama de Classes (v2):** Adicionar entidades e regras de Médico, Especialidade, Grade de Atendimento e Paciente.
- [x] **3. Diagramas de Sequência:** Criar os diagramas de sequência para UC4, UC5, UC6 e UC7.
- [x] **4. Revisar e ajustar Diagrama de Classes:** Refinar assinaturas, validações (RN01, RN02) e associações após análise dos diagramas de sequência.
- [x] **5. Desenvolver o código:** Implementar cadastros, buscas e edições de médicos e pacientes.
- [x] **6. Preparar incremento:** Consolidar o Diagrama de Classes para receber o Ciclo 3.

### Notas do Ciclo 2
- **Passo 1 concluído (Escopo definido):**
  - **UC4 (Cadastrar Médico — Administrador):** nome completo, CRM, UF do CRM, especialidade única (catálogo pré-populado no banco) e grade de atendimento (um turno com hora inicial e hora final por dia da semana, exigindo ao menos 1 dia e `horaFinal > horaInicial`). Valida unicidade de `CRM + UF` (RN02) e grava como *Ativo*.
  - **UC5 (Editar Médico — Administrador):** listagem de todos os médicos (incluindo *Inativos*), edição de dados, especialidade, grade e situação (*Ativo*/*Inativo*) com validação de `CRM + UF` (RN02) e confirmação antes de salvar.
  - **UC6 (Cadastrar Paciente — Recepcionista):** CPF (11 dígitos, único pela RN01), nome completo, data de nascimento (não futura), sexo e telefone; grava como *Ativo*. Em caso de CPF duplicado, exibe nome e situação do paciente existente sem recadastrar.
  - **UC7 (Consultar e Editar Paciente — Recepcionista):** busca por CPF ou parte do nome, visualização com CPF bloqueado para edição (RN01), alteração de dados e/ou situação (incluindo reativação) com confirmação antes de salvar.
  - **Fora do Ciclo 2 (integrado no Ciclo 3):** validação da RN08 para bloquear alteração de grade/inativação de médico (UC5) e inativação de paciente (UC7) quando houver consultas futuras *Agendadas*, pois a entidade `Consulta` será introduzida no Ciclo 3.
- **Passo 2 concluído:** Gerado [diagrama_classes_v2.puml](diagramas/classes/diagrama_classes_v2.puml) incrementando a v1 com `Medico`, `Especialidade`, `GradeAtendimento`, `Paciente`, enums (`Situacao`, `Sexo`, `DiaSemana`), além de `MedicoController`, `PacienteController`, `MedicoView` e `PacienteView`.
- **Passo 3 concluído:** Gerados os diagramas de sequência UML do Ciclo 2: [uc4_cadastrar_medico.puml](diagramas/sequencia/uc4_cadastrar_medico.puml), [uc5_editar_medico.puml](diagramas/sequencia/uc5_editar_medico.puml), [uc6_cadastrar_paciente.puml](diagramas/sequencia/uc6_cadastrar_paciente.puml) e [uc7_consultar_editar_paciente.puml](diagramas/sequencia/uc7_consultar_editar_paciente.puml), com `strictuml`, ativações explícitas, mensagens síncronas/retorno (`-->>`), `<<create>>` e fragmentos `alt`/`note`.
- **Revisão do Passo 2 (antes do Passo 3):** [diagrama_classes_v2.puml](diagramas/classes/diagrama_classes_v2.puml) ajustado:
  - **Validar antes de confirmar (UC5 e UC7):** incluídos `validarMedico(...)` e `validarPaciente(...)` nos Controllers e `enviarEdicao(...)` em `MedicoView` e `PacienteView`. Fluxo previsto: `enviarEdicao` → `validar...` → `solicitarConfirmacao()` → `confirmarEdicao` → `editar...` (que pode validar de novo antes de gravar).
  - **Sem duplicação em `Medico`:** removidos os atributos `especialidade` e `grades`, que passaram a ser nomes de papel nas associações (`-especialidade` e `-grades`). Getters e setters mantidos.
  - **Multiplicidade da grade:** `Medico "1" *--> "1..7" GradeAtendimento` (um turno por dia da semana, no máximo 7).
  - **Setas para enums:** de 17 para 3. Ficaram só as dos Controllers que usam valor fixo (`RecepcionistaController ..> Perfil`, `MedicoController ..> Situacao` e `PacienteController ..> Situacao`). Nos demais casos o enum já aparece como tipo de atributo ou parâmetro.
  - **Imagem:** PNG gerado de novo com 3539 px de largura (antes passava do limite de 4096 px do PlantUML e cortava a `PacienteView`).
  - **Convenção:** em `existeCrmUf(crm, ufCrm, ignorarId)`, o cadastro (UC4) passa `ignorarId = 0`.
- **Revisão do Passo 4 (diagramas de sequência × diagrama de classes v2):**
  - **UC5 e UC7 validam antes de confirmar:** os diagramas passaram a usar `enviarEdicao` → `validarMedico`/`validarPaciente` → `solicitarConfirmacao()` → `confirmarEdicao` → `editarMedico`/`editarPaciente`, seguindo a ordem do caso de uso (validar, confirmar, gravar). O `existeCrmUf(crm, ufCrm, id)` foi para o `validarMedico`.
  - **`GradeAtendimento.isHorarioValido()` em uso:** UC4 e UC5 têm um `loop` que pergunta a cada grade se o horário é válido, em vez de o Controller testar `horaFinal > horaInicial`.
  - **UC5 usa `buscarMedico(id)`:** ao selecionar o médico, a View carrega o registro completo (especialidade e grade) antes de exibir o formulário.
  - **Removido `PacienteController.buscarPaciente(id)`** da v2: a lista do UC7 já traz todos os dados do paciente.
  - **`<<create>>` no ponto certo:** `novoMedico` (UC4) e `novoPaciente` (UC6) não são mais declarados no topo, então aparecem na altura da criação.
  - **UC6:** a mensagem de CPF duplicado volta como uma única `String` com nome e situação do paciente existente, conforme o retorno de `cadastrarPaciente`.
  - Sem ajustes em associações, atributos, classes ou multiplicidades.
- **Passo 5 concluído:** Implementados schema MySQL do Ciclo 2 (`especialidades` pré-populada com 12 itens, `medicos`, `grades_atendimento` com `ON DELETE CASCADE` e `pacientes` em `database/schema.sql`), back-end MVC fiel ao `diagrama_classes_v2.puml` e aos diagramas de sequência/atividade de UC4–UC7 (`Situacao`, `Sexo`, `DiaSemana`, `Especialidade`, `GradeAtendimento`, `Medico`, `Paciente`, `MedicoController`, `PacienteController` e rotas HTTP em `backend/server.py`) e front-end Vue 3 + Tailwind CSS + DaisyUI (`MedicoView.vue`, `PacienteView.vue`, `services/api.js` e navegação por perfil em `App.vue`). Validado com 32 testes unitários/API (14 do Ciclo 1 + 18 do Ciclo 2), build de produção (`frontend/dist`) via `frontend/build.ps1` e teste ponta a ponta (UC4, UC5, UC6 e UC7) no `MySQL80` real.
- **Passo 6 concluído (auditoria código × diagramas × requisitos, UC4 a UC7):**
  - Conformes: visibilidade (atributos privados), assinaturas, navegabilidade (`Medico` → `Especialidade` e `GradeAtendimento`, sem volta), multiplicidades (`setEspecialidade` exige 1 e `setGrades` exige de 1 a 7 dias sem repetição), composição (`Medico` cria cópias próprias das grades e as regrava em `salvar()`), ordem das chamadas, `<<create>>` dentro do Controller e `alt`/`loop` como `if`/`for`. Sem atalhos nem lógica vazada.
  - Ajustes: nota "revalida antes de gravar" em [uc5_editar_medico.puml](diagramas/sequencia/uc5_editar_medico.puml) e [uc7_consultar_editar_paciente.puml](diagramas/sequencia/uc7_consultar_editar_paciente.puml), porque `editarMedico`/`editarPaciente` chamam `validar...` de novo; `server.py` ganhou `_converter_hora` próprio e deixou de chamar o método interno `GradeAtendimento._converter_horario`; a nota de infraestrutura da v2 passou a listar os auxiliares internos de Model, Controller e View.
  - Regras extras aceitas por caírem em "Dados inválidos": UF fora das 27, dia repetido na grade e especialidade inexistente.
  - 32 testes passando. [diagrama_classes_v2.puml](diagramas/classes/diagrama_classes_v2.puml) consolidado para receber o Ciclo 3 (pendência: RN08).

---

## Ciclo 3: Núcleo de Agendamento e Cancelamento (UC8, UC9)

**Objetivo:** Entregar o fluxo principal do sistema: consultar horários livres na grade do médico, agendar consultas sem conflito e cancelar consultas.

- [x] **1. Definir escopo do ciclo:** UC8 (Agendar Consulta), UC9 (Cancelar Consulta) + integração da RN08 em UC5 e UC7.
- [x] **2. Incrementar Diagrama de Classes (v3):** Adicionar `Consulta` e métodos de cálculo de horários livres e verificação de conflitos (RN04, RN05, RN07, RN08).
- [x] **3. Diagramas de Sequência:** Criar os diagramas de sequência para UC8 e UC9.
- [x] **4. Revisar e ajustar Diagrama de Classes:** Refinar o diagrama após análise dos fluxos de agendamento e cancelamento.
- [x] **5. Desenvolver o código:** Implementar agenda de horários livres, agendamento, cancelamento e travas da RN08 em médicos/pacientes.
- [x] **6. Preparar incremento:** Consolidar o Diagrama de Classes para receber o Ciclo 4.

### Notas do Ciclo 3
- *Lembrar:* Consultas passadas são tratadas por verificação temporal (`dataHora < agora`), sem rotina em segundo plano (RN03).
- **Passo 1 concluído (Escopo definido):**
  - **UC8 (Agendar Consulta — Recepcionista):** busca de paciente por CPF/nome, verificação de paciente *Ativo* (RN08), seleção de médico *Ativo* e data, cálculo e listagem de horários livres da grade do médico na data (RN06, RN07, duração padrão da clínica RNF04, excluindo horários já ocupados pela RN04), verificação de conflito de horário do paciente (RN05) e gravação da `Consulta` como *Agendada* com lembrete *Pendente*.
  - **UC9 (Cancelar Consulta — Recepcionista):** busca de paciente, listagem de consultas futuras (`dataHora > agora`) *Agendadas* do paciente (RN03, RN06), exibição dos dados da consulta com solicitação de motivo opcional e alteração para *Cancelada* mediante confirmação.
  - **Integração da RN08 em UC5 e UC7:** bloquear alteração de grade ou inativação de médico (`MedicoController.validarMedico` / `editarMedico`) e inativação de paciente (`PacienteController.validarPaciente` / `editarPaciente`) quando houver consultas futuras *Agendadas*.
  - **Fora do Ciclo 3 (integrado no Ciclo 4):** entidade `Ausencia` (UC11), bloqueio de horários por ausência na agenda do UC8 (RN07/RN10) e envio de lembretes via WhatsApp (UC10 / RN09).
- **Passo 2 concluído:** Gerado [diagrama_classes_v3.puml](diagramas/classes/diagrama_classes_v3.puml) incrementando a v2 com os enums `StatusConsulta` e `StatusLembrete`, a entidade `Consulta` (associações unidirecionais `0..* --> 1` para `Paciente` e `Medico`, sem duplicar papéis como atributos), `GradeAtendimento.gerarHorarios(duracaoMinutos)`, `Medico.listarAtivos()`, `ConsultaController`, `ConsultaView` e dependências de RN08 em `MedicoController` e `PacienteController`.
- **Passo 3 concluído:** Gerados os diagramas de sequência UML do Ciclo 3: [uc8_agendar_consulta.puml](diagramas/sequencia/uc8_agendar_consulta.puml) e [uc9_cancelar_consulta.puml](diagramas/sequencia/uc9_cancelar_consulta.puml), com `strictuml`, ativações explícitas, mensagens síncronas/retorno (`-->>`), `<<create>>` no momento da instanciação e fragmentos `alt`/`opt`/`note`.
- **Passo 4 concluído (sequência × classes v3 × requisitos):**
  - **Diagrama de classes:** incluído `Medico.getGradeDoDia(data: Date): GradeAtendimento`. O próprio `Medico` encontra a grade do dia da semana, e o Controller não precisa conhecer `DiaSemana`.
  - **UC8 alinhado à v3:** a busca de pacientes usa `PacienteController.consultarPacientes`; o paciente Ativo é verificado por `ConsultaController.verificarPaciente` (antes era a View); os médicos ativos só são listados após o paciente ser aprovado e aparecem por `exibirMedicos`.
  - **UC8, `agendarConsulta`:** a nota virou chamadas: `verificarPaciente` (RN08), `listarHorariosLivres` para conferir se o horário escolhido continua livre, futuro e dentro da grade (RN04, RN06, RN07) e `existeConflitoPaciente` (RN05).
  - **UC9:** busca pelo `PacienteController`; antes de cancelar, confere se a consulta existe, está *Agendada* e é futura (RN03, RN06); o motivo é gravado só se informado (`opt`).
  - **RN08 em UC5 e UC7:** as notas de pendência viraram chamadas. `validarMedico` chama `Consulta.existeFuturaPorMedico(id)` quando a grade muda ou o médico é inativado; `validarPaciente` chama `Consulta.listarFuturasAgendadasPorPaciente(id)` quando o paciente é inativado.
- **Revisão pré-Passo 5 (auditoria entre diagramas de classes, sequência e atividade):**
  - **UC8 ([uc8_agendar_consulta.puml](diagramas/sequencia/uc8_agendar_consulta.puml)):** alinhado ao diagrama de atividade (`cu08`) para recarregar os horários livres (`listarHorariosLivres` + `exibirHorariosLivres`) quando `agendarConsulta` retorna conflito/indisponibilidade; ordenadas as validações de `agendarConsulta` (`verificarPaciente` → `listarHorariosLivres` → `existeConflitoPaciente`) preservando a mensagem de paciente inativo; modeladas as chamadas `medico.getNome()`, `medico.getEspecialidade()` e `especialidade.getNome()` para compor a confirmação; adicionadas guardas `opt != null` antes de `getSituacao()`.
  - **UC9 ([uc9_cancelar_consulta.puml](diagramas/sequencia/uc9_cancelar_consulta.puml)):** adicionada guarda `opt consulta != null` antes de `getStatus()` e `getDataHora()`.
  - **UC5 ([uc5_editar_medico.puml](diagramas/sequencia/uc5_editar_medico.puml)):** adicionada guarda `alt medico == null` após `Medico.buscarPorId(id)` em `validarMedico` e explicitada em nota a comparação de `grades` e `gradesAtuais` por valor (`diaSemana`, `horaInicial` e `horaFinal`).
  - **Classes v3 ([diagrama_classes_v3.puml](diagramas/classes/diagrama_classes_v3.puml)):** incluídas as dependências `ConsultaView ..> Especialidade` e `ConsultaController ..> Especialidade`, e detalhada na nota de infraestrutura a comparação de grades no Controller.
- **Passo 5 concluído:** Implementados schema MySQL da tabela `consultas` (`database/schema.sql`), back-end MVC fiel ao `diagrama_classes_v3.puml` e aos diagramas de sequência/atividade de UC8, UC9, UC5 e UC7 (`StatusConsulta`, `StatusLembrete`, `Consulta`, `GradeAtendimento.gerarHorarios`, `Medico.getGradeDoDia`, `Medico.listarAtivos`, `ConsultaController`, travas da RN08 em `MedicoController` e `PacienteController`, e rotas HTTP em `backend/server.py`) e front-end Vue 3 + Tailwind CSS + DaisyUI (`ConsultaView.vue`, `ConsultaControllerApi` em `services/api.js` e habilitação da aba *Consultas* em `App.vue`). Validado com 42 testes unitários/API (14 do Ciclo 1 + 18 do Ciclo 2 + 10 do Ciclo 3) e build de produção (`frontend/dist`) via `frontend/build.ps1`.
- **Passo 6 concluído (auditoria código × diagramas × requisitos, UC8, UC9 e RN08 em UC5/UC7):**
  - Conformes: atributos privados de `Consulta`, assinaturas e estáticos da v3, navegabilidade `Consulta` → `Paciente`/`Medico` sem volta, multiplicidade 1 garantida em `setPaciente`/`setMedico` e `salvar()`, ordem das chamadas de `listarHorariosLivres`, `agendarConsulta` e `cancelarConsulta`, `<<create>>` no Controller, `opt` do motivo e travas da RN08. Sem atalhos nem regra de negócio na View.
  - Ajustes: `Consulta` ganhou `_converter_data` próprio e deixou de chamar o método interno `Paciente._converter_data`; a data/hora atual da clínica (RNF03) passou a vir de uma única função, `config.agora_clinica()`, usada por `Consulta`, `ConsultaController` e `PacienteController`.
  - Aceito por estar fora do escopo: não há trava no banco contra duas reservas simultâneas do mesmo horário (controle de concorrência está em "Fora do Escopo").
  - 42 testes passando. [diagrama_classes_v3.puml](diagramas/classes/diagrama_classes_v3.puml) consolidado para receber o Ciclo 4 (pendências: `Ausencia`/RN10 e lembretes/RN09).

---

## Ciclo 4: Lembretes via WhatsApp e Ausências Médicas (UC10, UC11)

**Objetivo:** Finalizar o produto com a fila de lembretes via WhatsApp (`wa.me`) e o registro de ausências médicas com bloqueio de agenda.

- [x] **1. Definir escopo do ciclo:** UC10 (Enviar Lembrete de Consulta), UC11 (Registrar Ausência do Médico).
- [x] **2. Incrementar Diagrama de Classes (v4 - Final):** Adicionar `Ausencia`, configurações da clínica (RNF04) e atualizar a lógica de horários livres para considerar ausências (RN07, RN09, RN10).
- [x] **3. Diagramas de Sequência:** Criar os diagramas de sequência para UC10 e UC11.
- [x] **4. Revisar e ajustar Diagrama de Classes:** Revisão final de consistência entre todos os diagramas e requisitos.
- [x] **5. Desenvolver o código:** Implementar envio de lembretes via link WhatsApp, registro de ausências e bloqueio na agenda do UC8.

### Notas do Ciclo 4
- **Passo 1 concluído (Escopo definido):**
  - **UC10 (Enviar Lembrete de Consulta — Recepcionista):** listagem cronológica de consultas futuras (`dataHora > agora`) *Agendadas* com lembrete *Pendente* (RN09), montagem da mensagem padrão usando os dados da consulta e as configurações da clínica (RNF04: `nomeClinica` e `telefoneClinica`), abertura do WhatsApp (`wa.me`) com o telefone do paciente e a mensagem preenchida (sem integração por API) e marcação do lembrete como *Enviado* mediante confirmação da Recepcionista.
  - **UC11 (Registrar Ausência do Médico — Recepcionista):** seleção de médico *Ativo*, listagem das ausências futuras já registradas (`dataFinal >= hoje`), preenchimento de `motivo`, `dataInicial` e `dataFinal` (em dias inteiros) com validação de campos obrigatórios, datas não passadas (RN06), `dataFinal >= dataInicial` e inexistência de consultas futuras *Agendadas* para o médico no período (RN10), gravação mediante confirmação.
  - **Integração no UC8 (RN07 e RN10):** atualizar `ConsultaController.listarHorariosLivres` (e a revalidação de `agendarConsulta`) para bloquear todos os horários de datas cobertas por uma ausência registrada (`Ausencia.existeAusenciaNaData`).
- **Passo 2 concluído:** Gerado [diagrama_classes_v4.puml](diagramas/classes/diagrama_classes_v4.puml) incrementando a v3 com:
  - **Model:** entidade `Ausencia` (associação unidirecional `0..* --> "-medico\n1" Medico` sem duplicar papel como atributo, `isPeriodoValido()`, `listarFuturasPorMedico(medicoId)` e `existeAusenciaNaData(medicoId, data)`), classe `ConfiguracaoClinica` (RNF04: `nomeClinica`, `telefoneClinica`, `duracaoConsultaMinutos` e `{static} obter()`) e novos métodos estáticos em `Consulta` (`existeFuturaPorMedicoNoPeriodo(medicoId, dataInicial, dataFinal)` para RN10 e `listarLembretesPendentes()` para RN09).
  - **Controller e View:** `LembreteController` e `LembreteView` (UC10), `AusenciaController` e `AusenciaView` (UC11), além das dependências de `ConsultaController` para `Ausencia` (RN07/RN10) e `ConfiguracaoClinica` (RNF04).
- **Passo 3 concluído:** Gerados os diagramas de sequência UML do Ciclo 4 ([uc10_enviar_lembrete.puml](diagramas/sequencia/uc10_enviar_lembrete.puml) e [uc11_registrar_ausencia.puml](diagramas/sequencia/uc11_registrar_ausencia.puml)) com `strictuml`, ativações explícitas, mensagens síncronas/retorno (`-->>`), `<<create>>` no momento da instanciação e fragmentos `alt`/`opt`/`note`, e atualizado [uc8_agendar_consulta.puml](diagramas/sequencia/uc8_agendar_consulta.puml) para integrar `Ausencia.existeAusenciaNaData` (RN07/RN10) e `ConfiguracaoClinica.obter()` (RNF04).
- **Revisão do Passo 2 (antes do Passo 3):** [diagrama_classes_v4.puml](diagramas/classes/diagrama_classes_v4.puml) ajustado:
  - **Sem busca duplicada:** removido `AusenciaController.listarMedicosAtivos()`; a `AusenciaView` reutiliza `ConsultaController.listarMedicosAtivos()` (nova dependência `AusenciaView ..> ConsultaController`), como foi feito com `consultarPacientes` na v3.
  - **Nota de infraestrutura:** passa a dizer que a mensagem padrão do UC10 é montada dentro de `LembreteController.gerarLinkWhatsApp`, e que `Ausencia.isPeriodoValido()` confere só `dataFinal >= dataInicial` (datas passadas/RN06 e RN10 ficam em `AusenciaController.validarAusencia`).
  - **Imagem:** a largura natural era 5460 px (acima do limite de 4096 px do PlantUML). Com `skinparam nodesep 10` e duas ligações ocultas que põem `LembreteView` e `AusenciaView` numa segunda linha do pacote View, o PNG ficou com 3868 px, inteiro e com fonte 11.
  - **Lembrete para o Passo 3:** no UC8, `listarHorariosLivres` deve chamar `Ausencia.existeAusenciaNaData(medicoId, data)`, e a nota de pendência do Ciclo 4 sai.
- **Passo 4 concluído (sequência × classes v4 × requisitos):**
  - **UC11:** a lista de médicos ativos passou a vir de `ConsultaController.listarMedicosAtivos()`, como prevê a v4 (o método tinha saído do `AusenciaController`).
  - **Diagrama de classes:** removido `Ausencia.isPeriodoValido()`, que nenhum fluxo usa (a validação do UC11 acontece antes de existir o objeto, em `validarAusencia`); a nota de infraestrutura foi ajustada. Incluído `Consulta.isLembretePendente(): boolean` (Agendada, lembrete Pendente e futura — RN09), que substitui no UC10 as consultas a `getStatus`, `getLembrete` e `getDataHora` repetidas em `gerarLinkWhatsApp` e `confirmarEnvio`. Removida a seta `LembreteController ..> StatusConsulta`, que deixou de ser usada.
  - **UC10:** notas dizendo que, depois de confirmar (passo 6) ou de desistir (5a), a View chama `listarLembretesPendentes()` de novo e volta ao passo 1.
  - **Imagens:** gerados `uc10_enviar_lembrete.png` e `uc11_registrar_ausencia.png`, e gerado de novo o `uc8_agendar_consulta.png` (estava desatualizado). O UC8 passava de 4096 px de altura; com `skinparam defaultFontSize 11` ficou com 3995 px, inteiro. A v4 ficou com 3818 px de largura.
  - **Lembrete para o Passo 5:** a duração da consulta deve vir de `ConfiguracaoClinica.obter().getDuracaoConsultaMinutos()`, e não mais direto de `config.CONSULTA_DURACAO_MINUTOS`.
- **Passo 5 concluído:** Implementados schema MySQL da tabela `ausencias` (`database/schema.sql`), back-end MVC fiel ao `diagrama_classes_v4.puml` e aos diagramas de sequência/atividade de UC10, UC11 e UC8 (`Ausencia`, `ConfiguracaoClinica`, novos métodos em `Consulta`, `LembreteController`, `AusenciaController`, integração de `Ausencia.existeAusenciaNaData` e `ConfiguracaoClinica.obter()` em `ConsultaController`, e rotas HTTP em `backend/server.py`) e front-end Vue 3 + Tailwind CSS + DaisyUI (`LembreteView.vue`, `AusenciaView.vue`, `LembreteControllerApi`/`AusenciaControllerApi` em `services/api.js` e habilitação das abas *Lembretes* e *Ausências* em `App.vue`). Validado com 52 testes unitários/API (14 do Ciclo 1 + 18 do Ciclo 2 + 10 do Ciclo 3 + 10 do Ciclo 4) e build de produção (`frontend/dist`) via `frontend/build.ps1`.
- **Revisão geral do código (UC1 a UC11 × diagramas × requisitos):** sem desvios em relação à v4, aos diagramas de sequência e às regras RN01–RN11/RNF01–RNF04. Ajustes de limpeza:
  - **Erros internos:** as 26 respostas HTTP 500 do `server.py` deixaram de devolver o texto da exceção ao navegador; agora passam por `_enviar_erro_interno`, que imprime o detalhe no console do servidor e devolve uma mensagem genérica.
  - **Código sem uso:** removido o ramo `UPDATE` de `Ausencia.salvar()`, já que nenhum caso de uso edita ausências.
  - Aceitos por estarem no "Fora do Escopo" ou por decisão de projeto: sem controle de concorrência nem expiração de sessão; duração da consulta fixa na instalação (RNF04).
  - 52 testes passando (14 + 18 + 10 + 10).
- *Entrega final:* Validar todos os 11 casos de uso de ponta a ponta no navegador.
- **Validação de ponta a ponta no navegador (23/11/2026, `MySQL80` real, `http://localhost:8000`):** os 11 casos de uso funcionaram, com os fluxos principais e as extensões testadas:
  - **UC1:** login inválido (3a) e login do Administrador e da Recepcionista, cada um com as abas do seu perfil.
  - **UC2/UC3:** login já utilizado (3b), cadastro, nome vazio (5a) e edição.
  - **UC4/UC5:** CRM + UF duplicado (3b/5b), grade com hora final menor que a inicial (3a), cadastro com 7 dias, edição com modal de confirmação aberto só depois da validação, e bloqueio da inativação do médico com consulta futura (RN08).
  - **UC6/UC7:** data de nascimento futura (3a), CPF duplicado mostrando nome e situação (3b, inclusive digitado com máscara), "Paciente não localizado" (2a), CPF bloqueado na edição, edição confirmada, inativação bloqueada com consulta futura (RN08) e permitida depois do cancelamento.
  - **UC8:** data passada sem horários, 8 horários de 30 min na grade, agendamento com data, hora, médico e especialidade na confirmação, horário ocupado deixando de aparecer (RN04), conflito do paciente com outro médico no mesmo horário (RN05/8a, com recarga dos horários), dia com ausência sem horários (RN07/RN10) e paciente inativo bloqueado (4a).
  - **UC9:** cancelamento com motivo e "Nenhuma consulta para cancelar" (4a).
  - **UC10:** link `wa.me` com 55 + telefone e a mensagem padrão do requisito, "Não Enviei" mantendo Pendente (5a) e confirmação retirando a consulta da lista. A abertura da aba do WhatsApp foi simulada (o `window.open` foi substituído para registrar a URL, sem abrir o site).
  - **UC11:** bloqueio por consulta no período (RN10/5b), período inválido (5a), confirmação e listagem da ausência registrada.
  - Sem erro de JavaScript no console nem erro 500 no servidor; os erros no console são as respostas 400/401/409 esperadas dos testes negativos.
  - **Dados de teste deixados no banco:** recepcionista `e2e.recep`, médico "Dr. Teste E2E" (CRM 990011/RS), "Paciente Teste E2E" (CPF 999.000.111-22, Inativo), uma consulta Cancelada em 24/11/2026 e uma ausência em 25/11/2026.

---

## Decisões Técnicas e Arquiteturais
- **Front-end:** HTML, Tailwind CSS, Vue, DaisyUI (tema `autumn`), gerenciado com Vite.
- **Back-end:** Python puro (`http.server`) sem framework web + driver MySQL (`mysql-connector-python`).
- **Banco de Dados:** MySQL.
- **Padrão Arquitetural:** MVC enxuto (`View` $\rightarrow$ `Controller` $\rightarrow$ `Model`).
- **Diagrama de Classes:** Getters e setters explícitos.
