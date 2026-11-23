# Agenda Médica — Controle de Consultas

Sistema web para controle de agendamentos de consultas em clínica médica.

## Arquitetura
- **Front-end:** HTML, Tailwind CSS, Vue 3, DaisyUI (tema `autumn`), gerenciado com Vite (`frontend/`).
- **Back-end:** Python puro (`http.server`) + `mysql-connector-python` seguindo MVC enxuto (`backend/`).
- **Banco de Dados:** MySQL 8.0 (`database/schema.sql`).

## Como executar

### 1. Configurar o Back-end e o Banco de Dados
1. Copie `backend/.env.example` para `backend/.env` e informe suas credenciais do MySQL (`DB_USER`, `DB_PASSWORD`, etc.).
2. Instale a dependência do driver MySQL:
   ```powershell
   pip install -r backend/requirements.txt
   ```
3. Inicialize o banco de dados (`agenda_medica`) e o administrador padrão:
   ```powershell
   python backend/init_db.py
   ```
   - **Login inicial do Administrador:** `admin`
   - **Senha inicial:** `admin123`
4. Inicie o servidor back-end:
   ```powershell
   python backend/server.py
   ```

### 2. Executar ou recompilar o Front-end
**Opção A (recomendada quando o projeto estiver no Google Drive `G:\`):**
Para recompilar `frontend/dist` após editar arquivos `.vue`/`.js`/`.css` sem criar `node_modules` dentro do Google Drive:
```powershell
.\frontend\build.ps1
```
O `backend/server.py` serve automaticamente o `frontend/dist` atualizado em `http://127.0.0.1:8000`.

**Opção B (em disco local NTFS, com hot-reload do Vite):**
```powershell
cd frontend
npm install
npm run dev
```
Acesse `http://localhost:5173`.

### 3. Executar Testes Unitários (Ciclo 1)
```powershell
python -m unittest discover -s backend/tests -v
```
