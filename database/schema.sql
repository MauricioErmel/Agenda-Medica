-- ============================================================================
-- Agenda Médica - Schema do Banco de Dados (Ciclos 1, 2, 3 e 4: UC1 a UC11)
-- Banco de Dados: MySQL 8.0+
-- ============================================================================

CREATE DATABASE IF NOT EXISTS agenda_medica
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE agenda_medica;

-- ----------------------------------------------------------------------------
-- Ciclo 1: Usuários (Administradores e Recepcionistas)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(150) NOT NULL,
  login VARCHAR(80) NOT NULL,
  senha VARCHAR(255) NOT NULL,
  perfil ENUM('ADMINISTRADOR', 'RECEPCIONISTA') NOT NULL,
  criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT uk_usuarios_login UNIQUE (login)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Administrador padrão cadastrado diretamente na instalação (conforme item 1.2)
-- Credenciais iniciais: login = admin | senha = admin123
INSERT INTO usuarios (nome, login, senha, perfil)
VALUES (
  'Administrador do Sistema',
  'admin',
  'pbkdf2_sha256$100000$a1b2c3d4e5f60718293a4b5c6d7e8f90$44138abc921d1c95bb573a09516cd4c82e8271fc3d9604b7c5f7f1bf26b6292d',
  'ADMINISTRADOR'
)
ON DUPLICATE KEY UPDATE nome = nome;

-- ----------------------------------------------------------------------------
-- Ciclo 2: Especialidades, Médicos, Grades de Atendimento e Pacientes
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS especialidades (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(120) NOT NULL,
  CONSTRAINT uk_especialidades_nome UNIQUE (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO especialidades (nome)
VALUES
  ('Cardiologia'),
  ('Clínica Geral'),
  ('Dermatologia'),
  ('Endocrinologia'),
  ('Ginecologia e Obstetrícia'),
  ('Neurologia'),
  ('Oftalmologia'),
  ('Ortopedia e Traumatologia'),
  ('Otorrinolaringologia'),
  ('Pediatria'),
  ('Psiquiatria'),
  ('Urologia')
ON DUPLICATE KEY UPDATE nome = nome;

CREATE TABLE IF NOT EXISTS medicos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(150) NOT NULL,
  crm VARCHAR(20) NOT NULL,
  uf_crm CHAR(2) NOT NULL,
  especialidade_id INT NOT NULL,
  situacao ENUM('ATIVO', 'INATIVO') NOT NULL DEFAULT 'ATIVO',
  criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT uk_medicos_crm_uf UNIQUE (crm, uf_crm),
  CONSTRAINT fk_medicos_especialidade FOREIGN KEY (especialidade_id) REFERENCES especialidades(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS grades_atendimento (
  id INT AUTO_INCREMENT PRIMARY KEY,
  medico_id INT NOT NULL,
  dia_semana ENUM('SEGUNDA', 'TERCA', 'QUARTA', 'QUINTA', 'SEXTA', 'SABADO', 'DOMINGO') NOT NULL,
  hora_inicial TIME NOT NULL,
  hora_final TIME NOT NULL,
  CONSTRAINT uk_grades_medico_dia UNIQUE (medico_id, dia_semana),
  CONSTRAINT fk_grades_medico FOREIGN KEY (medico_id) REFERENCES medicos(id) ON DELETE CASCADE,
  CONSTRAINT ck_grades_horario CHECK (hora_final > hora_inicial)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS pacientes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cpf CHAR(11) NOT NULL,
  nome VARCHAR(150) NOT NULL,
  data_nascimento DATE NOT NULL,
  sexo ENUM('MASCULINO', 'FEMININO', 'OUTRO') NOT NULL,
  telefone VARCHAR(20) NOT NULL,
  situacao ENUM('ATIVO', 'INATIVO') NOT NULL DEFAULT 'ATIVO',
  criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT uk_pacientes_cpf UNIQUE (cpf)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Ciclo 3: Consultas (Agendamento e Cancelamento — UC8 e UC9)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS consultas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  paciente_id INT NOT NULL,
  medico_id INT NOT NULL,
  data_hora DATETIME NOT NULL,
  status ENUM('AGENDADA', 'CANCELADA') NOT NULL DEFAULT 'AGENDADA',
  lembrete ENUM('PENDENTE', 'ENVIADO') NOT NULL DEFAULT 'PENDENTE',
  motivo_cancelamento VARCHAR(500) NULL,
  criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_consultas_medico_data (medico_id, data_hora, status),
  INDEX idx_consultas_paciente_data (paciente_id, data_hora, status),
  CONSTRAINT fk_consultas_paciente FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
  CONSTRAINT fk_consultas_medico FOREIGN KEY (medico_id) REFERENCES medicos(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Ciclo 4: Ausências Médicas (UC11 / RN07, RN10)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ausencias (
  id INT AUTO_INCREMENT PRIMARY KEY,
  medico_id INT NOT NULL,
  motivo VARCHAR(500) NOT NULL,
  data_inicial DATE NOT NULL,
  data_final DATE NOT NULL,
  criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_ausencias_medico_periodo (medico_id, data_inicial, data_final),
  CONSTRAINT fk_ausencias_medico FOREIGN KEY (medico_id) REFERENCES medicos(id),
  CONSTRAINT ck_ausencias_periodo CHECK (data_final >= data_inicial)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
