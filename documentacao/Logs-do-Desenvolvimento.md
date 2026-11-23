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

- [ ] **1. Definir escopo do ciclo:** CU4 (Cadastrar Médico), CU5 (Editar Médico), CU6 (Cadastrar Paciente), CU7 (Consultar e Editar Paciente).
- [ ] **2. Incrementar Diagrama de Classes (v2):** Adicionar entidades e regras de Médico, Especialidade, Grade de Atendimento e Paciente.
- [ ] **3. Diagramas de Sequência:** Criar os diagramas de sequência para CU4, CU5, CU6 e CU7.
- [ ] **4. Revisar e ajustar Diagrama de Classes:** Refinar assinaturas, validações (RN01, RN02) e associações após análise dos diagramas de sequência.
- [ ] **5. Desenvolver o código:** Implementar cadastros, buscas e edições de médicos e pacientes.
- [ ] **6. Preparar incremento:** Consolidar o Diagrama de Classes para receber o Ciclo 3.

### Notas do Ciclo 2
- *Pendência planejada:* A validação da RN08 no CU5 (alterar grade/inativar médico) e no CU7 (inativar paciente) depende de consultas futuras *Agendadas*, portanto será completada e integrada no **Ciclo 3**.

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
