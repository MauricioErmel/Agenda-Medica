# Logs do Desenvolvimento — Controle de Consultas

Este documento acompanha os ciclos iterativos (estilo Sprint) de modelagem UML (Diagrama de Classes e Diagramas de Sequência) e implementação do sistema **Agenda Médica**.

---

## Visão Geral dos Ciclos

O desenvolvimento foi dividido em **4 Ciclos**, agrupando os 11 casos de uso por dependência funcional:

| Ciclo | Foco | Casos de Uso |
|---|---|---|
| **Ciclo 1** | Autenticação e Gestão de Recepcionistas | CU1, CU2, CU3 |
| **Ciclo 2** | Cadastros Base (Médicos e Pacientes) | CU4, CU5, CU6, CU7 |
| **Ciclo 3** | Núcleo de Agendamento e Cancelamento | CU8, CU9 |
| **Ciclo 4** | Lembretes via WhatsApp e Ausências Médicas | CU10, CU11 |

---

## Ciclo 1: Autenticação e Gestão de Recepcionistas (CU1, CU2, CU3)

**Objetivo:** Estruturar a base do projeto e entregar o login de usuários (Administrador e Recepcionista) além do cadastro/edição de recepcionistas.

- [x] **1. Definir escopo do ciclo:** CU1 (Entrar no Sistema), CU2 (Cadastrar Recepcionista), CU3 (Editar Recepcionista).
- [x] **2. Diagrama de Classes (v1):** Modelar as classes iniciais com base no `Levantamento_de_Requisitos.md`.
- [x] **3. Diagramas de Sequência:** Criar os diagramas de sequência para CU1, CU2 e CU3.
- [x] **4. Revisar e ajustar Diagrama de Classes:** Refinar atributos, métodos e relacionamentos após análise dos diagramas de sequência.
- [x] **5. Desenvolver o código:** Implementar autenticação e CRUD de recepcionistas.
- [x] **6. Preparar incremento:** Consolidar o Diagrama de Classes para receber o Ciclo 2.

### Notas do Ciclo 1
- Gerado [diagrama_classes_v1.puml](diagramas/classes/diagrama_classes_v1.puml) no padrão MVC enxuto com getters e setters explícitos.
- Gerados os diagramas de sequência UML do Ciclo 1: [cu1_entrar_no_sistema.puml](diagramas/sequencia/cu1_entrar_no_sistema.puml), [cu2_cadastrar_recepcionista.puml](diagramas/sequencia/cu2_cadastrar_recepcionista.puml) e [cu3_editar_recepcionista.puml](diagramas/sequencia/cu3_editar_recepcionista.puml).
- Revisado e ajustado [diagrama_classes_v1.puml](diagramas/classes/diagrama_classes_v1.puml) para alinhar métodos de entrada/cancelamento nas Views, construtor explícito em `Usuario` e dependências `View ..> Usuario`.
- Passo 4 revisado contra os diagramas de sequência (associações, métodos, atributos, responsabilidades, classes e multiplicidade): removido `getSenha()` de `Usuario` (a senha só é usada dentro de `autenticar()` e `salvar()`) e incluída a dependência `RecepcionistaController ..> Perfil` (usa `Perfil.RECEPCIONISTA` no CU2). Demais critérios sem ajustes.
- Passo 5 concluído: implementado schema MySQL (`database/schema.sql`), back-end MVC em Python puro (`backend/model`, `backend/controller`, `backend/server.py`, `backend/init_db.py`) e front-end Vue 3 + Tailwind CSS + DaisyUI tema `autumn` (`frontend/`). Validado com 14 testes unitários/API e teste ponta a ponta (CU1, CU2 e CU3) no `MySQL80` real.
- Passo 6 concluído: código auditado contra os diagramas de classes e de sequência (visibilidade, assinaturas, estáticos, navegabilidade, multiplicidade, `<<create>>`, ordem das chamadas, `alt`/`opt` e retornos). Ajustes:
  - Código: `LoginView.exibirMenu(perfil)` passou a ter a assinatura do diagrama; o parâmetro extra `manterMensagem` de `acionarEdicaoRecepcionista()` virou o auxiliar interno `carregarLista()`.
  - Diagramas: `exibirMensagem(mensagem, tipo)` em `RecepcionistaView` (classes, CU2 e CU3), `to_dict()` em `Usuario` e nota sobre a infraestrutura não modelada (API HTTP, `Database` e auxiliares internos).
  - Mantidas sem modelar, por serem validações defensivas: `AuthController.entrar()` recusa login/senha vazios sem consultar o banco, e `editarRecepcionista()` recusa id inexistente ou de Administrador.
  - 14 testes do back-end passando. O `frontend/dist` precisa ser gerado de novo (`npm install` e `npm run build`) para refletir os ajustes do front-end.
- Próximo passo: iniciar o Ciclo 2 (CU4 a CU7).

---

## Ciclo 2: Cadastros Base — Médicos e Pacientes (CU4, CU5, CU6, CU7)

**Objetivo:** Permitir o cadastro, consulta e edição de médicos (com especialidade única e grade de atendimento) e pacientes.

- [x] **1. Definir escopo do ciclo:** CU4 (Cadastrar Médico), CU5 (Editar Médico), CU6 (Cadastrar Paciente), CU7 (Consultar e Editar Paciente).
- [x] **2. Incrementar Diagrama de Classes (v2):** Adicionar entidades e regras de Médico, Especialidade, Grade de Atendimento e Paciente.
- [x] **3. Diagramas de Sequência:** Criar os diagramas de sequência para CU4, CU5, CU6 e CU7.
- [x] **4. Revisar e ajustar Diagrama de Classes:** Refinar assinaturas, validações (RN01, RN02) e associações após análise dos diagramas de sequência.
- [x] **5. Desenvolver o código:** Implementar cadastros, buscas e edições de médicos e pacientes.
- [x] **6. Preparar incremento:** Consolidar o Diagrama de Classes para receber o Ciclo 3.

### Notas do Ciclo 2
- **Passo 1 concluído (Escopo definido):**
  - **CU4 (Cadastrar Médico — Administrador):** nome completo, CRM, UF do CRM, especialidade única (catálogo pré-populado no banco) e grade de atendimento (um turno com hora inicial e hora final por dia da semana, exigindo ao menos 1 dia e `horaFinal > horaInicial`). Valida unicidade de `CRM + UF` (RN02) e grava como *Ativo*.
  - **CU5 (Editar Médico — Administrador):** listagem de todos os médicos (incluindo *Inativos*), edição de dados, especialidade, grade e situação (*Ativo*/*Inativo*) com validação de `CRM + UF` (RN02) e confirmação antes de salvar.
  - **CU6 (Cadastrar Paciente — Recepcionista):** CPF (11 dígitos, único pela RN01), nome completo, data de nascimento (não futura), sexo e telefone; grava como *Ativo*. Em caso de CPF duplicado, exibe nome e situação do paciente existente sem recadastrar.
  - **CU7 (Consultar e Editar Paciente — Recepcionista):** busca por CPF ou parte do nome, visualização com CPF bloqueado para edição (RN01), alteração de dados e/ou situação (incluindo reativação) com confirmação antes de salvar.
  - **Fora do Ciclo 2 (integrado no Ciclo 3):** validação da RN08 para bloquear alteração de grade/inativação de médico (CU5) e inativação de paciente (CU7) quando houver consultas futuras *Agendadas*, pois a entidade `Consulta` será introduzida no Ciclo 3.
- **Passo 2 concluído:** Gerado [diagrama_classes_v2.puml](diagramas/classes/diagrama_classes_v2.puml) incrementando a v1 com `Medico`, `Especialidade`, `GradeAtendimento`, `Paciente`, enums (`Situacao`, `Sexo`, `DiaSemana`), além de `MedicoController`, `PacienteController`, `MedicoView` e `PacienteView`.
- **Passo 3 concluído:** Gerados os diagramas de sequência UML do Ciclo 2: [cu4_cadastrar_medico.puml](diagramas/sequencia/cu4_cadastrar_medico.puml), [cu5_editar_medico.puml](diagramas/sequencia/cu5_editar_medico.puml), [cu6_cadastrar_paciente.puml](diagramas/sequencia/cu6_cadastrar_paciente.puml) e [cu7_consultar_editar_paciente.puml](diagramas/sequencia/cu7_consultar_editar_paciente.puml), com `strictuml`, ativações explícitas, mensagens síncronas/retorno (`-->>`), `<<create>>` e fragmentos `alt`/`note`.
- **Revisão do Passo 2 (antes do Passo 3):** [diagrama_classes_v2.puml](diagramas/classes/diagrama_classes_v2.puml) ajustado:
  - **Validar antes de confirmar (CU5 e CU7):** incluídos `validarMedico(...)` e `validarPaciente(...)` nos Controllers e `enviarEdicao(...)` em `MedicoView` e `PacienteView`. Fluxo previsto: `enviarEdicao` → `validar...` → `solicitarConfirmacao()` → `confirmarEdicao` → `editar...` (que pode validar de novo antes de gravar).
  - **Sem duplicação em `Medico`:** removidos os atributos `especialidade` e `grades`, que passaram a ser nomes de papel nas associações (`-especialidade` e `-grades`). Getters e setters mantidos.
  - **Multiplicidade da grade:** `Medico "1" *--> "1..7" GradeAtendimento` (um turno por dia da semana, no máximo 7).
  - **Setas para enums:** de 17 para 3. Ficaram só as dos Controllers que usam valor fixo (`RecepcionistaController ..> Perfil`, `MedicoController ..> Situacao` e `PacienteController ..> Situacao`). Nos demais casos o enum já aparece como tipo de atributo ou parâmetro.
  - **Imagem:** PNG gerado de novo com 3539 px de largura (antes passava do limite de 4096 px do PlantUML e cortava a `PacienteView`).
  - **Convenção:** em `existeCrmUf(crm, ufCrm, ignorarId)`, o cadastro (CU4) passa `ignorarId = 0`.
- **Revisão do Passo 4 (diagramas de sequência × diagrama de classes v2):**
  - **CU5 e CU7 validam antes de confirmar:** os diagramas passaram a usar `enviarEdicao` → `validarMedico`/`validarPaciente` → `solicitarConfirmacao()` → `confirmarEdicao` → `editarMedico`/`editarPaciente`, seguindo a ordem do caso de uso (validar, confirmar, gravar). O `existeCrmUf(crm, ufCrm, id)` foi para o `validarMedico`.
  - **`GradeAtendimento.isHorarioValido()` em uso:** CU4 e CU5 têm um `loop` que pergunta a cada grade se o horário é válido, em vez de o Controller testar `horaFinal > horaInicial`.
  - **CU5 usa `buscarMedico(id)`:** ao selecionar o médico, a View carrega o registro completo (especialidade e grade) antes de exibir o formulário.
  - **Removido `PacienteController.buscarPaciente(id)`** da v2: a lista do CU7 já traz todos os dados do paciente.
  - **`<<create>>` no ponto certo:** `novoMedico` (CU4) e `novoPaciente` (CU6) não são mais declarados no topo, então aparecem na altura da criação.
  - **CU6:** a mensagem de CPF duplicado volta como uma única `String` com nome e situação do paciente existente, conforme o retorno de `cadastrarPaciente`.
  - Sem ajustes em associações, atributos, classes ou multiplicidades.
- **Passo 5 concluído:** Implementados schema MySQL do Ciclo 2 (`especialidades` pré-populada com 12 itens, `medicos`, `grades_atendimento` com `ON DELETE CASCADE` e `pacientes` em `database/schema.sql`), back-end MVC fiel ao `diagrama_classes_v2.puml` e aos diagramas de sequência/atividade de CU4–CU7 (`Situacao`, `Sexo`, `DiaSemana`, `Especialidade`, `GradeAtendimento`, `Medico`, `Paciente`, `MedicoController`, `PacienteController` e rotas HTTP em `backend/server.py`) e front-end Vue 3 + Tailwind CSS + DaisyUI (`MedicoView.vue`, `PacienteView.vue`, `services/api.js` e navegação por perfil em `App.vue`). Validado com 32 testes unitários/API (14 do Ciclo 1 + 18 do Ciclo 2), build de produção (`frontend/dist`) via `frontend/build.ps1` e teste ponta a ponta (CU4, CU5, CU6 e CU7) no `MySQL80` real.
- **Passo 6 concluído (auditoria código × diagramas × requisitos, CU4 a CU7):**
  - Conformes: visibilidade (atributos privados), assinaturas, navegabilidade (`Medico` → `Especialidade` e `GradeAtendimento`, sem volta), multiplicidades (`setEspecialidade` exige 1 e `setGrades` exige de 1 a 7 dias sem repetição), composição (`Medico` cria cópias próprias das grades e as regrava em `salvar()`), ordem das chamadas, `<<create>>` dentro do Controller e `alt`/`loop` como `if`/`for`. Sem atalhos nem lógica vazada.
  - Ajustes: nota "revalida antes de gravar" em [cu5_editar_medico.puml](diagramas/sequencia/cu5_editar_medico.puml) e [cu7_consultar_editar_paciente.puml](diagramas/sequencia/cu7_consultar_editar_paciente.puml), porque `editarMedico`/`editarPaciente` chamam `validar...` de novo; `server.py` ganhou `_converter_hora` próprio e deixou de chamar o método interno `GradeAtendimento._converter_horario`; a nota de infraestrutura da v2 passou a listar os auxiliares internos de Model, Controller e View.
  - Regras extras aceitas por caírem em "Dados inválidos": UF fora das 27, dia repetido na grade e especialidade inexistente.
  - 32 testes passando. [diagrama_classes_v2.puml](diagramas/classes/diagrama_classes_v2.puml) consolidado para receber o Ciclo 3 (pendência: RN08).

---

## Ciclo 3: Núcleo de Agendamento e Cancelamento (CU8, CU9)

**Objetivo:** Entregar o fluxo principal do sistema: consultar horários livres na grade do médico, agendar consultas sem conflito e cancelar consultas.

- [ ] **1. Definir escopo do ciclo:** CU8 (Agendar Consulta), CU9 (Cancelar Consulta) + integração da RN08 em CU5 e CU7.
- [ ] **2. Incrementar Diagrama de Classes (v3):** Adicionar `Consulta` e métodos de cálculo de horários livres e verificação de conflitos (RN04, RN05, RN07, RN08).
- [ ] **3. Diagramas de Sequência:** Criar os diagramas de sequência para CU8 e CU9.
- [ ] **4. Revisar e ajustar Diagrama de Classes:** Refinar o diagrama após análise dos fluxos de agendamento e cancelamento.
- [ ] **5. Desenvolver o código:** Implementar agenda de horários livres, agendamento, cancelamento e travas da RN08 em médicos/pacientes.
- [ ] **6. Preparar incremento:** Consolidar o Diagrama de Classes para receber o Ciclo 4.

### Notas do Ciclo 3
- *Lembrar:* Consultas passadas são tratadas por verificação temporal (`dataHora < agora`), sem rotina em segundo plano (RN03).

---

## Ciclo 4: Lembretes via WhatsApp e Ausências Médicas (CU10, CU11)

**Objetivo:** Finalizar o produto com a fila de lembretes via WhatsApp (`wa.me`) e o registro de ausências médicas com bloqueio de agenda.

- [ ] **1. Definir escopo do ciclo:** CU10 (Enviar Lembrete de Consulta), CU11 (Registrar Ausência do Médico).
- [ ] **2. Incrementar Diagrama de Classes (v4 - Final):** Adicionar `Ausencia`, configurações da clínica (RNF04) e atualizar a lógica de horários livres para considerar ausências (RN07, RN09, RN10).
- [ ] **3. Diagramas de Sequência:** Criar os diagramas de sequência para CU10 e CU11.
- [ ] **4. Revisar e ajustar Diagrama de Classes:** Revisão final de consistência entre todos os diagramas e requisitos.
- [ ] **5. Desenvolver o código:** Implementar envio de lembretes via link WhatsApp, registro de ausências e bloqueio na agenda do CU8.

### Notas do Ciclo 4
- *Entrega final:* Validar todos os 11 casos de uso de ponta a ponta no navegador.

---

## Decisões Técnicas e Arquiteturais
- **Front-end:** HTML, Tailwind CSS, Vue, DaisyUI (tema `autumn`), gerenciado com Vite.
- **Back-end:** Python puro (`http.server`) sem framework web + driver MySQL (`mysql-connector-python`).
- **Banco de Dados:** MySQL.
- **Padrão Arquitetural:** MVC enxuto (`View` $\rightarrow$ `Controller` $\rightarrow$ `Model`).
- **Diagrama de Classes:** Getters e setters explícitos.
