-- ============================================================================
-- Agenda Médica - Schema Inicial (Ciclo 1: CU1, CU2, CU3)
-- Banco de Dados: MySQL 8.0+
-- ============================================================================

CREATE DATABASE IF NOT EXISTS agenda_medica
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE agenda_medica;

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
