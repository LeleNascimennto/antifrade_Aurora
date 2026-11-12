# Tutorial simples — Banco Aurora no Windows (sem venv)

Este guia usa **PowerShell**, **Python instalado no Windows** e o **Docker Desktop** com o container PostgreSQL **`Postgre-TECH`**, que você já criou. Não será criado outro container.

> Execute os comandos na raiz do projeto (onde ficam `app/`, `sql/`, `config.py` e `requirements.txt`). Mantenha o Docker Desktop aberto.

## 1. Verificar Python e Docker

```powershell
python --version
docker --version
docker ps -a
```

O projeto espera Python de **3.10 a 3.13**. Confira se `Postgre-TECH` aparece na lista.

## 2. Iniciar seu container existente

```powershell
docker start Postgre-TECH
docker ps
```

Se ele já estiver iniciado, basta continuar. Confira na coluna `PORTS` se a porta **5432** do container está publicada como **localhost:5432** (por exemplo, `0.0.0.0:5432->5432/tcp`). Se a porta do Windows for diferente, ajuste `PG_PORT` e a URL do MLflow nos passos seguintes.

> Os próximos comandos assumem que o container possui PostgreSQL com usuário `postgres`, senha `postgres` e acesso pela porta 5432. **Um container já existente pode ter credenciais diferentes**: confira as configurações dele no Docker Desktop antes de prosseguir. Não é necessário recriá-lo.

## 3. Instalar as dependências sem venv

```powershell
python -m pip install -r requirements.txt
```

As bibliotecas serão instaladas no Python que você está usando no Windows. Se houver erro de permissão, confira sua instalação do Python antes de prosseguir.

## 4. Configurar o `.env`

Se ainda não existir `.env`:

```powershell
Copy-Item .env.exemplo .env
```

Abra o arquivo:

```powershell
notepad .env
```

Confira as variáveis existentes e ajuste seus valores para a conexão real do container:

```dotenv
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_SENHA=postgres
MLFLOW_TRACKING_URI=http://127.0.0.1:5000
SISTEMA_URL=http://127.0.0.1:8000
```

**Não apague as demais variáveis do `.env`.** Se seu PostgreSQL usa outra senha, usuário ou porta, use os valores reais. Não publique o `.env` no Git.

Teste a configuração:

```powershell
python config.py
```

## 5. Criar os bancos e as tabelas

Use o `psql` dentro do container existente, sem instalar PostgreSQL no Windows:

```powershell
Get-Content -Raw sql/01_criar_bancos.sql | docker exec -i Postgre-TECH psql -U postgres -d postgres
```

```powershell
Get-Content -Raw sql/02_criar_tabelas.sql | docker exec -i Postgre-TECH psql -U postgres -d antifraude
```

Verifique as tabelas:

```powershell
docker exec Postgre-TECH psql -U postgres -d antifraude -c "\dt"
```

Devem aparecer seis tabelas: `decisoes`, `lotes`, `predicoes`, `rotulos`, `transacoes` e `trocas_modelo`.

> Se o usuário do PostgreSQL não for `postgres`, substitua `-U postgres` pelo usuário correto. Se os bancos já existirem, o script de criação pode avisar sobre isso; verifique o resultado antes de continuar.

## 6. Iniciar o MLflow — Terminal 1

Abra um terminal PowerShell na raiz do projeto e execute:

```powershell
python -m mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri postgresql://postgres:postgres@localhost:5432/mlflow --default-artifact-root ./mlruns
```

Mantenha o terminal aberto. Acesse **http://127.0.0.1:5000**.

> Ajuste usuário, senha e porta na URL `postgresql://...` se forem diferentes. Senhas com caracteres especiais exigem codificação adequada na URL.

## 7. Iniciar a aplicação — Terminal 2

Abra **outro** PowerShell na raiz do projeto:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Mantenha este terminal aberto. Acesse:

- Aplicação: http://127.0.0.1:8000
- Documentação da API: http://127.0.0.1:8000/docs

## 8. Testar — Terminal 3

Abra mais um terminal e execute:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/saude
Invoke-RestMethod http://127.0.0.1:8000/api/modelo
```

Antes de registrar o modelo, a API pode informar que não há modelo em produção. Isso é esperado.

## 9. Registrar o modelo da Parte 1

Com PostgreSQL, MLflow e aplicação funcionando, execute:

```powershell
python -m jupyter notebook parte1.ipynb
```

Execute as células do notebook em ordem. O resultado esperado no tutorial original é o modelo `antifraude` com alias `champion`, tag `threshold=0.05` e custo de validação de **R$ 28.448,23**.

## 10. Nas próximas vezes (resumo rápido)

Você **não precisa reinstalar as bibliotecas nem recriar os bancos** a cada execução.

**Primeiro**, abra o Docker Desktop e inicie o container:

```powershell
docker start Postgre-TECH
```

**Terminal 1 — MLflow:**

```powershell
python -m mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri postgresql://postgres:lelelovebts12@localhost:5432/mlflow --default-artifact-root ./mlruns
```

**Terminal 2 — aplicação:**

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Acesse **http://127.0.0.1:8000**.

## Encerrar

Pressione **Ctrl+C** nos terminais da aplicação e do MLflow. Para parar o PostgreSQL:

```powershell
docker stop Postgre-TECH
```

## Problemas comuns

- **`connection refused` na porta 5432:** confira `docker ps` e a porta publicada pelo container.
- **`password authentication failed`:** confira usuário e senha reais do PostgreSQL, `.env` e comando do MLflow.
- **`No module named ...`:** instale as dependências com `python -m pip install -r requirements.txt`.
- **MLflow não responde:** confirme que o Terminal 1 continua aberto e acesse http://127.0.0.1:5000/health.
- **Sem modelo em produção:** execute o notebook da Parte 1 para registrar o alias `champion`.

---

**Importante:** usar Python sem `venv` é possível, mas as dependências ficam no ambiente Python do Windows e podem conflitar com outros projetos. Neste tutorial, somente o PostgreSQL roda no Docker.
