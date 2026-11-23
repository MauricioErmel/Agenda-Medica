# Sistema de Agenda de Consultas para Clínica Médica


## 1. Visão Geral

### 1.1 Escopo

Sistema que roda no navegador e permite à equipe de uma clínica médica controlar o agendamento de consultas: cadastro de pacientes, marcação e cancelamento de consultas, lembretes aos pacientes via WhatsApp e gestão da agenda dos médicos.

- Cada instalação atende **uma única clínica**.
- O sistema **não** realiza cobrança, não registra prontuário e não é acessado por pacientes nem por médicos.

### 1.2 Atores

- **Recepcionista:** cadastra, consulta, edita e inativa pacientes, agenda e cancela consultas, envia lembretes e registra ausências dos médicos.
- **Administrador:** cadastra e edita recepcionistas e médicos, e define a grade de atendimento dos médicos.

**Observações**

- Paciente e Médico não acessam o sistema, portanto não são atores. O médico comunica ausências à clínica por meio externo.
- O WhatsApp é aberto no dispositivo da Recepcionista, sem integração por API, portanto não é modelado como ator.
- Os Administradores são permanentes e cadastrados diretamente no banco de dados na instalação, fora do escopo dos casos de uso.

### 1.3 Casos de Uso por Ator

| Nº | Caso de Uso | Ator Principal |
|----|-------------|----------------|
| CU1 | Entrar no Sistema | Recepcionista, Administrador |
| CU2 | Cadastrar Recepcionista | Administrador |
| CU3 | Editar Recepcionista | Administrador |
| CU4 | Cadastrar Médico | Administrador |
| CU5 | Editar Médico | Administrador |
| CU6 | Cadastrar Paciente | Recepcionista |
| CU7 | Consultar e Editar Paciente | Recepcionista |
| CU8 | Agendar Consulta | Recepcionista |
| CU9 | Cancelar Consulta | Recepcionista |
| CU10 | Enviar Lembrete de Consulta | Recepcionista |
| CU11 | Registrar Ausência do Médico | Recepcionista |

### 1.4 Glossário

- **Grade de atendimento:** turno de horário (hora inicial e hora final) em que o médico atende em cada dia da semana. Definida pelo Administrador (CU4, CU5). A duração das consultas é padrão da clínica.
- **Horário:** cada intervalo agendável calculado a partir da grade e da duração padrão da consulta. Não é armazenado; aparece como *livre*, *ocupado* (há consulta *Agendada*) ou *bloqueado* (há ausência na data).
- **Ausência:** período (data inicial e data final, em dias inteiros) em que o médico não atende. Registrada pela Recepcionista (CU11).
- **Consulta:** vínculo entre paciente, médico e data/hora. Estados: *Agendada* ou *Cancelada* (consultas com `dataHora < agora` são identificadas por verificação temporal como passadas).
- **Lembrete:** campo da consulta com valor *Pendente* ou *Enviado*.
- **Situação:** médicos e pacientes são *Ativos* ou *Inativos*. Registros nunca são excluídos.
- **Especialidade:** item do catálogo de especialidades. Cada médico possui uma única especialidade.

### 1.5 Regras de Negócio

- **RN01:** o CPF do paciente deve conter 11 dígitos e ser único entre todos os pacientes. Um paciente *Inativo* é reativado (CU7), não recadastrado. O CPF não pode ser alterado.
- **RN02:** a combinação CRM + UF é única entre todos os médicos.
- **RN03:** a consulta possui estado *Agendada* ou *Cancelada*. Uma consulta é considerada passada quando `dataHora < agora`. O cancelamento pode registrar um motivo opcional em texto.
- **RN04:** um horário comporta no máximo uma consulta *Agendada*.
- **RN05:** um paciente não pode ter duas consultas *Agendadas* no mesmo horário.
- **RN06:** só horários futuros (`dataHora > agora`) podem ser agendados ou cancelados, e ausências só podem ser registradas a partir da data atual.
- **RN07:** um horário só é oferecido para agendamento se pertencer à grade de um médico *Ativo* na data selecionada, estiver livre (sem consulta *Agendada* nem ausência registrada) e for futuro.
- **RN08:** nenhum registro é excluído; usa-se inativação (médicos e pacientes) ou cancelamento (consultas). Paciente *Inativo* não recebe agendamentos e não pode ser inativado se tiver consultas futuras *Agendadas*. Médico *Inativo* não recebe agendamentos e não pode ser inativado nem ter sua grade alterada se tiver consultas futuras *Agendadas*.
- **RN09 (lembrete):** aparecem para lembrete as consultas futuras *Agendadas* com lembrete *Pendente*.
- **RN10:** uma ausência tem motivo, data inicial e data final (dias inteiros, com data final igual ou posterior à inicial) e não pode ser registrada se houver consultas futuras *Agendadas* para o médico no período.
- **RN11:** o login é único entre todos os usuários (Recepcionistas e Administradores).

### 1.6 Requisitos Não Funcionais

- **RNF01:** acesso por navegador (Chrome, Edge e Firefox), interface em português do Brasil.
- **RNF02:** acesso por login e senha.
- **RNF03:** datas e horas seguem o fuso horário da clínica.
- **RNF04:** nome, telefone da clínica e duração padrão da consulta são configurados na instalação.

### 1.7 Fora do Escopo

- Cobrança, convênios e pagamentos.
- Lista de espera.
- Integração por API com o WhatsApp e envio automático de mensagens.
- Reagendamento como operação única (faz-se CU8 e depois CU9).
- Cancelamento automático em lote de consultas (consultas afetadas devem ser canceladas antes via CU9).
- Registro de comparecimento/falta e prontuário.
- Acesso de pacientes e médicos.
- Cadastro e redefinição de senha de administradores (feitos diretamente no banco de dados).
- Auditoria e registro de logs.
- Controles avançados de segurança (bloqueio por tentativas, expiração de sessão, senha provisória) e controle de concorrência.

*Os textos de mensagens entre aspas são ilustrativos.*

---

## 2. Casos de Uso

## Caso de Uso 1: Entrar no Sistema

- **Objetivo:** Permitir a Recepcionistas e Administradores acessarem as funções do seu perfil.
- **Ator Principal:** Recepcionista ou Administrador.
- **Nível:** Objetivo do Usuário.
- **Partes Interessadas e Interesses:**
  - *Usuário:* acessar suas funcionalidades.
- **Gatilho:** O usuário abre o sistema.
- **Condições Prévias:** Nenhuma.
- **Condições Posteriores:**
  - **Sucesso:** O usuário está autenticado e vê as funções do seu perfil.
  - **Garantia Mínima:** Em caso de falha, o usuário não acessa o sistema.

### Fluxo Principal de Sucesso:
1. O sistema solicita login e senha.
2. O usuário informa suas credenciais.
3. O sistema verifica se o login existe e se a senha está correta.
4. O sistema libera as funções do perfil do usuário.

### Extensões (Fluxos Alternativos):
- **3a. Login ou senha inválidos:**
  - 3a1. O sistema informa "Login ou senha inválidos" e retorna ao passo 1.

---

## Caso de Uso 2: Cadastrar Recepcionista

- **Objetivo:** Permitir ao Administrador cadastrar uma nova Recepcionista.
- **Ator Principal:** Administrador.
- **Nível:** Objetivo do Usuário.
- **Partes Interessadas e Interesses:**
  - *Administrador:* dar acesso a novas colaboradoras.
- **Gatilho:** O Administrador aciona a opção de cadastrar Recepcionista.
- **Condições Prévias:** O Administrador está autenticado (CU1).
- **Condições Posteriores:**
  - **Sucesso:** A Recepcionista está gravada e pode entrar no sistema.
  - **Garantia Mínima:** Nada é gravado em caso de erro ou desistência.

### Fluxo Principal de Sucesso:
1. O sistema solicita nome completo, login e senha.
2. O Administrador informa os dados e solicita salvar.
3. O sistema valida os campos obrigatórios e a unicidade do login (RN11).
4. O sistema grava a Recepcionista e confirma: "Recepcionista cadastrada com sucesso!".

### Extensões (Fluxos Alternativos):
- **3a. Campos obrigatórios não preenchidos:**
  - 3a1. O sistema sinaliza os campos e retorna ao passo 1 mantendo os dados.
- **3b. Login já utilizado:**
  - 3b1. O sistema informa "Login já utilizado" e retorna ao passo 1 mantendo os dados.
- ***a. Desistência antes do passo 4:**
  - *a1. O sistema descarta os dados e encerra o caso de uso.

---

## Caso de Uso 3: Editar Recepcionista

- **Objetivo:** Permitir ao Administrador alterar o nome ou a senha de uma Recepcionista.
- **Ator Principal:** Administrador.
- **Nível:** Objetivo do Usuário.
- **Partes Interessadas e Interesses:**
  - *Administrador:* manter os dados da equipe atualizados e redefinir senha quando necessário.
- **Gatilho:** O Administrador aciona a opção de editar Recepcionista.
- **Condições Prévias:**
  - O Administrador está autenticado (CU1).
  - Existe ao menos uma Recepcionista cadastrada.
- **Condições Posteriores:**
  - **Sucesso:** As alterações estão gravadas.
  - **Garantia Mínima:** Sem confirmação, nada é alterado.

### Fluxo Principal de Sucesso:
1. O sistema lista as Recepcionistas (nome e login).
2. O Administrador seleciona uma Recepcionista.
3. O sistema exibe os dados atuais.
4. O Administrador altera o nome e/ou informa uma nova senha, e solicita salvar.
5. O sistema valida os campos obrigatórios.
6. O sistema grava as alterações e confirma: "Recepcionista atualizada com sucesso!".

### Extensões (Fluxos Alternativos):
- **5a. Dados inválidos:**
  - 5a1. O sistema sinaliza os campos e retorna ao passo 4 mantendo os dados.
- ***a. Desistência antes do passo 6:**
  - *a1. O sistema descarta as alterações e encerra o caso de uso.

---

## Caso de Uso 4: Cadastrar Médico

- **Objetivo:** Permitir ao Administrador cadastrar um médico com sua especialidade e grade de atendimento.
- **Ator Principal:** Administrador.
- **Nível:** Objetivo do Usuário.
- **Partes Interessadas e Interesses:**
  - *Administrador:* disponibilizar novos profissionais.
  - *Recepcionista:* ver os horários do médico para agendar.
- **Gatilho:** O Administrador aciona a opção de cadastrar médico.
- **Condições Prévias:**
  - O Administrador está autenticado (CU1).
  - Existe ao menos uma especialidade no catálogo.
- **Condições Posteriores:**
  - **Sucesso:** O médico está gravado como *Ativo* e seus horários aparecem para agendamento (CU8).
  - **Garantia Mínima:** Nada é gravado em caso de erro ou desistência.

### Fluxo Principal de Sucesso:
1. O sistema solicita nome completo, CRM, UF do CRM, especialidade e grade de atendimento (um turno com hora inicial e hora final para cada dia da semana em que atende).
2. O Administrador informa os dados e solicita salvar.
3. O sistema valida os campos obrigatórios (ao menos um dia na grade), a coerência dos horários (hora final maior que a inicial) e a unicidade de CRM + UF (RN02).
4. O sistema grava o médico como *Ativo* e confirma: "Médico cadastrado com sucesso!".

### Extensões (Fluxos Alternativos):
- **3a. Dados inválidos ou grade incoerente:**
  - 3a1. O sistema sinaliza os campos e retorna ao passo 1 mantendo os dados.
- **3b. CRM + UF já cadastrado:**
  - 3b1. O sistema informa "CRM já cadastrado no sistema" e retorna ao passo 1 mantendo os dados.
- ***a. Desistência antes do passo 4:**
  - *a1. O sistema descarta os dados e encerra o caso de uso.

---

## Caso de Uso 5: Editar Médico

- **Objetivo:** Permitir ao Administrador alterar dados, especialidade, grade ou situação de um médico.
- **Ator Principal:** Administrador.
- **Nível:** Objetivo do Usuário.
- **Partes Interessadas e Interesses:**
  - *Administrador:* manter o quadro médico atualizado.
- **Gatilho:** O Administrador aciona a opção de editar médico.
- **Condições Prévias:**
  - O Administrador está autenticado (CU1).
  - Existe ao menos um médico cadastrado.
- **Condições Posteriores:**
  - **Sucesso:** Os dados do médico estão atualizados.
  - **Garantia Mínima:** Sem confirmação, nada é alterado.

### Fluxo Principal de Sucesso:
1. O sistema lista os médicos (nome, CRM/UF, especialidade e situação), incluindo os *Inativos*.
2. O Administrador seleciona um médico.
3. O sistema exibe os dados atuais, especialidade, grade e situação.
4. O Administrador altera os dados desejados e solicita salvar.
5. O sistema valida os campos obrigatórios, a coerência da grade e a unicidade de CRM + UF (RN02). Se houver alteração na grade ou inativação do médico, verifica se não existem consultas futuras *Agendadas* (RN08).
6. O sistema solicita confirmação.
7. O Administrador confirma.
8. O sistema grava as alterações e confirma: "Médico atualizado com sucesso!".

### Extensões (Fluxos Alternativos):
- **5a. Dados inválidos ou grade incoerente:**
  - 5a1. O sistema sinaliza os campos e retorna ao passo 4 mantendo os dados.
- **5b. CRM + UF já pertence a outro médico:**
  - 5b1. O sistema informa "CRM já cadastrado no sistema" e retorna ao passo 4.
- **5c. Alteração de grade ou inativação com consultas futuras Agendadas:**
  - 5c1. O sistema informa que é preciso cancelar as consultas futuras antes (CU9) e retorna ao passo 4.
- ***a. Desistência antes do passo 8:**
  - *a1. O sistema descarta as alterações e encerra o caso de uso.

---

## Caso de Uso 6: Cadastrar Paciente

- **Objetivo:** Permitir à Recepcionista cadastrar um novo paciente.
- **Ator Principal:** Recepcionista.
- **Nível:** Objetivo do Usuário.
- **Partes Interessadas e Interesses:**
  - *Recepcionista:* registrar o paciente rapidamente durante o atendimento.
- **Gatilho:** A Recepcionista aciona a opção de cadastrar paciente.
- **Condições Prévias:** A Recepcionista está autenticada (CU1).
- **Condições Posteriores:**
  - **Sucesso:** O paciente está cadastrado como *Ativo* e pode ser agendado.
  - **Garantia Mínima:** Nada é gravado em caso de erro ou desistência.

### Fluxo Principal de Sucesso:
1. O sistema solicita os dados obrigatórios do paciente: CPF, nome completo, data de nascimento, sexo e telefone.
2. A Recepcionista informa os dados e solicita salvar.
3. O sistema valida os campos obrigatórios, a data de nascimento (não futura) e o CPF (11 dígitos e único — RN01).
4. O sistema grava o paciente como *Ativo* e confirma: "Paciente cadastrado com sucesso!".

### Extensões (Fluxos Alternativos):
- **3a. Campos obrigatórios vazios ou inválidos:**
  - 3a1. O sistema sinaliza os campos e retorna ao passo 1 mantendo os dados.
- **3b. CPF já cadastrado:**
  - 3b1. O sistema informa "CPF já cadastrado no sistema", mostrando nome e situação do paciente existente.
  - 3b2. A Recepcionista corrige o CPF (retorna ao passo 1) ou desiste.
- ***a. Desistência antes do passo 4:**
  - *a1. O sistema descarta os dados e encerra o caso de uso.

---

## Caso de Uso 7: Consultar e Editar Paciente

- **Objetivo:** Permitir à Recepcionista ver os dados de um paciente, alterá-los (exceto CPF) e alterar sua situação.
- **Ator Principal:** Recepcionista.
- **Nível:** Objetivo do Usuário.
- **Partes Interessadas e Interesses:**
  - *Recepcionista:* manter contatos atualizados e inativar pacientes que não devem mais ser agendados.
- **Gatilho:** A Recepcionista aciona a consulta de pacientes.
- **Condições Prévias:**
  - A Recepcionista está autenticada (CU1).
  - Existe ao menos um paciente cadastrado.
- **Condições Posteriores:**
  - **Sucesso:** Os dados foram exibidos e, se alterados, estão gravados.
  - **Garantia Mínima:** O CPF nunca é alterado; sem confirmação, nada é gravado.

### Fluxo Principal de Sucesso:
1. A Recepcionista informa o CPF ou parte do nome do paciente.
2. O sistema lista os pacientes encontrados (nome, data de nascimento, CPF e situação).
3. A Recepcionista seleciona o paciente.
4. O sistema exibe os dados do paciente, com o CPF bloqueado para edição.
5. A Recepcionista altera os dados e/ou a situação e solicita salvar.
6. O sistema valida os campos obrigatórios e, se for inativação, verifica que não há consultas futuras *Agendadas* (RN08).
7. O sistema solicita confirmação.
8. A Recepcionista confirma.
9. O sistema grava as alterações e confirma: "Dados do paciente atualizados com sucesso!".

### Extensões (Fluxos Alternativos):
- **2a. Nenhum paciente encontrado:**
  - 2a1. O sistema informa "Paciente não localizado" e retorna ao passo 1.
- **4a. Recepcionista só consulta os dados:**
  - 4a1. O caso de uso é encerrado sem alterações.
- **6a. Dados inválidos:**
  - 6a1. O sistema sinaliza os campos e retorna ao passo 5 mantendo os dados.
- **6b. Inativação com consultas futuras Agendadas:**
  - 6b1. O sistema informa que é preciso cancelar essas consultas antes (CU9) e retorna ao passo 5.
- ***a. Desistência antes do passo 9:**
  - *a1. O sistema descarta as alterações e encerra o caso de uso.

---

## Caso de Uso 8: Agendar Consulta

- **Objetivo:** Permitir à Recepcionista marcar uma consulta para um paciente *Ativo* em um horário livre.
- **Ator Principal:** Recepcionista.
- **Nível:** Objetivo do Usuário.
- **Partes Interessadas e Interesses:**
  - *Recepcionista:* agendar rapidamente sem choque de horário.
- **Gatilho:** A Recepcionista aciona a opção de agendar consulta.
- **Condições Prévias:**
  - A Recepcionista está autenticada (CU1).
  - Existe ao menos um médico *Ativo*.
- **Condições Posteriores:**
  - **Sucesso:** Existe uma consulta *Agendada*, com lembrete *Pendente*, e o horário aparece como ocupado.
  - **Garantia Mínima:** Em caso de erro ou desistência, a agenda não muda.

### Fluxo Principal de Sucesso:
1. A Recepcionista informa o CPF ou parte do nome do paciente.
2. O sistema lista os pacientes encontrados (nome, data de nascimento, CPF e situação).
3. A Recepcionista seleciona o paciente.
4. O sistema verifica que o paciente está *Ativo*.
5. A Recepcionista seleciona o médico *Ativo* e a data desejada.
6. O sistema lista os horários livres do médico naquela data (RN07).
7. A Recepcionista seleciona um horário e confirma.
8. O sistema verifica que o paciente não tem outra consulta *Agendada* no mesmo horário (RN05), grava a consulta como *Agendada* com lembrete *Pendente* e confirma: "Consulta agendada com sucesso", informando data, hora, médico e especialidade.

### Extensões (Fluxos Alternativos):
- **2a. Nenhum paciente encontrado:**
  - 2a1. O sistema informa "Paciente não localizado" e retorna ao passo 1.
- **4a. Paciente Inativo:**
  - 4a1. O sistema informa que pacientes inativos não podem ser agendados e retorna ao passo 1.
- **6a. Nenhum horário livre:**
  - 6a1. O sistema informa "Nenhum horário disponível" e retorna ao passo 5.
- **8a. Paciente já tem consulta no mesmo horário:**
  - 8a1. O sistema informa o conflito e retorna ao passo 6.
- ***a. Desistência antes do passo 8:**
  - *a1. O sistema não altera a agenda e encerra o caso de uso.

---

## Caso de Uso 9: Cancelar Consulta

- **Objetivo:** Permitir à Recepcionista cancelar uma consulta futura *Agendada*, liberando o horário.
- **Ator Principal:** Recepcionista.
- **Nível:** Objetivo do Usuário.
- **Partes Interessadas e Interesses:**
  - *Recepcionista:* liberar o horário e registrar, se desejar, o motivo do cancelamento.
- **Gatilho:** A Recepcionista aciona a opção de cancelar consulta.
- **Condições Prévias:** A Recepcionista está autenticada (CU1).
- **Condições Posteriores:**
  - **Sucesso:** A consulta está *Cancelada* e o horário voltou a ficar livre.
  - **Garantia Mínima:** Sem confirmação, a consulta não muda.

### Fluxo Principal de Sucesso:
1. A Recepcionista informa o CPF ou parte do nome do paciente.
2. O sistema lista os pacientes encontrados (nome, data de nascimento, CPF e situação).
3. A Recepcionista seleciona o paciente.
4. O sistema lista as consultas futuras *Agendadas* do paciente.
5. A Recepcionista seleciona a consulta.
6. O sistema exibe médico, especialidade, data e hora, e solicita um motivo opcional para o cancelamento.
7. A Recepcionista informa o motivo (se desejar) e confirma.
8. O sistema altera a consulta para *Cancelada*, grava o motivo (se informado) e confirma: "Consulta cancelada com sucesso!".

### Extensões (Fluxos Alternativos):
- **2a. Nenhum paciente encontrado:**
  - 2a1. O sistema informa "Paciente não localizado" e retorna ao passo 1.
- **4a. Paciente sem consultas futuras Agendadas:**
  - 4a1. O sistema informa "Nenhuma consulta para cancelar" e encerra o caso de uso.
- ***a. Desistência antes do passo 8:**
  - *a1. O sistema mantém a consulta e encerra o caso de uso.

---

## Caso de Uso 10: Enviar Lembrete de Consulta

- **Objetivo:** Permitir à Recepcionista enviar, via WhatsApp, lembretes de consultas futuras usando uma mensagem padrão montada pelo sistema.
- **Ator Principal:** Recepcionista.
- **Nível:** Objetivo do Usuário.
- **Partes Interessadas e Interesses:**
  - *Recepcionista:* reduzir faltas com pouco esforço.
- **Gatilho:** A Recepcionista aciona a lista de lembretes pendentes.
- **Condições Prévias:** A Recepcionista está autenticada (CU1).
- **Condições Posteriores:**
  - **Sucesso:** O lembrete da consulta está *Enviado* e a consulta saiu da lista de pendentes.
  - **Garantia Mínima:** Sem confirmação da Recepcionista, o lembrete continua *Pendente*.

### Fluxo Principal de Sucesso:
1. O sistema lista as consultas futuras *Agendadas* com lembrete *Pendente* (RN09), em ordem cronológica.
2. A Recepcionista seleciona uma consulta.
3. O sistema monta a mensagem padrão e abre o WhatsApp com o telefone do paciente e a mensagem preenchida.
4. A Recepcionista envia a mensagem no WhatsApp e volta ao sistema.
5. A Recepcionista confirma o envio.
6. O sistema marca o lembrete como *Enviado* e retira a consulta da lista.

#### Mensagem Padrão:
> [NOME DO PACIENTE], você possui uma consulta agendada na [NOME DA CLÍNICA] com [NOME DO MÉDICO] em [DATA E HORA DA CONSULTA].
> Caso você não possa comparecer, por favor, avise a clínica pelo telefone [TELEFONE DA CLÍNICA] para cancelar o agendamento.
> Se você for comparecer, não precisa fazer nada. Seu médico estará te aguardando.

### Extensões (Fluxos Alternativos):
- **1a. Nenhum lembrete pendente:**
  - 1a1. O sistema informa "Nenhuma consulta com lembrete pendente" e encerra o caso de uso.
- **5a. Envio não realizado:**
  - 5a1. A Recepcionista não confirma; o lembrete continua *Pendente* e o fluxo retorna ao passo 1.

---

## Caso de Uso 11: Registrar Ausência do Médico

- **Objetivo:** Permitir à Recepcionista registrar uma ausência de um médico em dias inteiros, bloqueando os horários do período.
- **Ator Principal:** Recepcionista.
- **Nível:** Objetivo do Usuário.
- **Partes Interessadas e Interesses:**
  - *Recepcionista:* bloquear a agenda quando o médico avisa que não atenderá.
- **Gatilho:** O médico comunica uma ausência e a Recepcionista aciona o registro.
- **Condições Prévias:**
  - A Recepcionista está autenticada (CU1).
  - Existe ao menos um médico *Ativo*.
- **Condições Posteriores:**
  - **Sucesso:** A ausência está gravada e os horários das datas do período aparecem bloqueados.
  - **Garantia Mínima:** Em caso de erro ou desistência, nada é gravado.

### Fluxo Principal de Sucesso:
1. O sistema lista os médicos *Ativos* (nome, CRM/UF e especialidade).
2. A Recepcionista seleciona um médico.
3. O sistema lista as ausências futuras já registradas para o médico.
4. A Recepcionista informa o motivo, a data inicial e a data final da ausência.
5. O sistema valida o motivo, que as datas não são passadas, que a data final é igual ou posterior à inicial e que não há consultas futuras *Agendadas* no período (RN10).
6. O sistema solicita confirmação.
7. A Recepcionista confirma.
8. O sistema grava a ausência e confirma: "Ausência registrada com sucesso!".

### Extensões (Fluxos Alternativos):
- **5a. Dados inválidos:**
  - 5a1. O sistema sinaliza o problema e retorna ao passo 4 mantendo os dados.
- **5b. Existem consultas futuras Agendadas no período:**
  - 5b1. O sistema informa que é preciso cancelar essas consultas antes (CU9) e retorna ao passo 4.
- ***a. Desistência antes do passo 8:**
  - *a1. O sistema descarta os dados e encerra o caso de uso.
