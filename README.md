# Banco Aurora — Projeto antifraude

O Banco Aurora usa um modelo para decidir quais transações Pix e de cartão bloquear. O custo de uma decisão é a soma do valor das fraudes aprovadas com R$ 15 por transação legítima bloqueada. O sistema bloqueia quando o score de fraude é maior ou igual ao limiar escolhido na validação.

Na Parte 1, a regressão logística e o Gradient Boosting foram treinados nas semanas 1 a 10 e avaliados nas semanas 11 e 12. O Gradient Boosting, com limiar de 0,05, foi registrado no MLflow como `antifraude@champion`. Seu custo na validação foi de R$ 28.448,23, frente a R$ 225.349,79 da regra de bloquear Pix acima de R$ 1.000. O modelo identificou 502 das 600 fraudes e bloqueou 563 transações legítimas.

## O que você precisa

- **Python 3.10 a 3.13**
- **O seu Postgres** (o container que você já usa nas aulas), com um usuário que possa criar bancos
- `psql` para rodar os scripts `.sql` (pode ser o do próprio container: `docker exec -i <container> psql ...`)

Ambiente virtual é **recomendado, não obrigatório**: organize a pasta como preferir. As versões do `requirements.txt` são as testadas. Se você instalar no Python global e houver conflito com outro projeto, o ajuste é seu.

## Passo a passo

### 1. Bancos e tabelas

Um servidor Postgres, dois bancos, como nas aulas: `antifraude` (o sistema) e `mlflow` (o MLflow).

```bash
psql -h localhost -U postgres -f sql/01_criar_bancos.sql
psql -h localhost -U postgres -d antifraude -f sql/02_criar_tabelas.sql
psql -h localhost -U postgres -d antifraude -c "\dt"     # tem que listar 6 tabelas
```

Se o Postgres estiver só dentro do container, sem a porta exposta:

```bash
docker exec -i <container> psql -U postgres < sql/01_criar_bancos.sql
docker exec -i <container> psql -U postgres -d antifraude < sql/02_criar_tabelas.sql
```

O `02_criar_tabelas.sql` é idempotente: rodar duas vezes não quebra nada.

### 2. Configuração

```powershell
Copy-Item .env.exemplo .env          # ajuste usuário, senha, host e porta do SEU Postgres
pip install -r requirements.txt
python config.py              # exibe as conexões e o comando do MLflow
```

### 3. MLflow (terminal 1)

O servidor do MLflow **não lê o `.env`**: a conexão vai na linha de comando. Use exatamente o comando que o `python config.py` imprimiu. Com os valores padrão:

```bash
python -m mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri postgresql://postgres:postgres@localhost:5432/mlflow --default-artifact-root ./mlruns
```

Abra http://127.0.0.1:5000.

Se aparecer `ImportError: cannot import name 'FallbackAsyncAdaptedQueuePool'`, rode `pip install "sqlalchemy<2.1"`.

### 4. Sistema (terminal 2)

Sempre a partir desta pasta (a raiz do projeto):

```bash
uvicorn app.main:app --reload --port 8000
```

Abra http://127.0.0.1:8000. Antes do seu primeiro modelo, o topo da tela mostra **"sem modelo em produção"** — é o esperado.

### 5. Notebook (terminal 3)

```bash
jupyter notebook parte1.ipynb
```

Rode o notebook **a partir desta pasta**, com o MLflow e o sistema no ar.

## Como o modelo entra em produção

O sistema usa sempre `models:/antifraude@champion`. Para isso, a versão registrada precisa:

1. **Receber as 13 features do contrato, cruas, na ordem do contrato.** Todo o pré-processamento mora dentro do modelo (um `Pipeline`). O sistema não transforma nada.
2. **Ter `predict_proba`.** Registre com `mlflow.sklearn.log_model`. Se o seu pipeline usa código seu (uma classe ou função do `features.py`), passe `code_paths=["features.py"]`, senão o sistema não consegue carregar o modelo.
3. **Ter a tag `threshold` na VERSÃO** (não na run), com o corte de bloqueio: `score >= threshold` bloqueia.
4. Opcional, mas cobrado na rastreabilidade: tag `motivo` na versão e uma descrição. O sistema anota o motivo em **Modelo → Histórico de trocas**.

Trocar o modelo em produção = mover o alias `champion` no MLflow. O sistema percebe na próxima chamada; não precisa reiniciar. Para aplicar o modelo novo a semanas já recebidas, use **Repontuar** na tela de Lotes.

## Estrutura do projeto

| Arquivo | O que é |
|---|---|
| `contrato/contrato_features.yaml` | O contrato de features v1.0. O sistema valida todo lote contra ele |
| `dados/` | Os dados da parte 1 (histórico rotulado, semanas 1 a 12) |
| `demanda_parte1.md` | O que o negócio pediu |
| `parte1.ipynb` | Notebook executado com treino, validação, registro no MLflow e teste de paridade da API |
| `features.py`, `monitoramento.py` | Pré-processamento, cálculo de custo, métricas e detecção de drift |
| `CHANGELOG.md` | O histórico de versões do seu modelo, mantido por você |
| `app/` | O sistema: API em FastAPI e front em HTML/CSS/JS puro (`app/static/`). Encanamento: vem pronto, não precisa mexer |
| `artefatos/parte1/` | Modelo exportado, evidências do MLflow e CSV de referência da validação |
| `sql/` | Criação dos bancos e das tabelas do sistema |
| `config.py`, `.env.exemplo` | Configuração das conexões |

Os CSVs de origem ficam em `dados/`, que é ignorada pelo Git. Em outro checkout, copie os dois CSVs da pasta-base do exercício para esse diretório antes de rodar o notebook.

## Como o sistema é montado

- **Back:** FastAPI (`app/main.py`), só API — devolve JSON e CSV.
- **Front:** HTML, CSS e JavaScript puros (`app/static/`), sem biblioteca. Cada página chama a API com `fetch`.
- O próprio FastAPI serve as páginas. A documentação automática das rotas fica em http://127.0.0.1:8000/docs.

| Página | O que faz | Rotas que ela chama |
|---|---|---|
| `/` | Painel do negócio, por semana: volume, % bloqueado e, quando há rótulo, fraude evitada, fraude perdida e custo | `GET /api/painel` |
| `/lotes` | Recebe o CSV de transações de uma semana; valida, grava e pontua. Também **Repontuar** e **baixar dados** | `GET/POST /api/lotes`, `POST /api/lotes/{n}/repontuar` |
| `/rotulos` | Recebe o CSV de contestações (rótulos) | `POST /api/rotulos` |
| `/modelo` | Quem está em produção, threshold e histórico de trocas | `GET /api/modelo` |
| `/decisoes` | Seu registro de decisões, por semana, e exportação | `GET/POST /api/decisoes` |
| todas | O selo do modelo no topo | `GET /api/saude` |

Outras rotas úteis:

| Rota | O que faz |
|---|---|
| `POST /predict` | Pontua transações avulsas (lista de JSON com as 13 features) |
| `GET /api/semanas/{n}/dados.csv` | Transações da semana + score vigente + rótulo (quando houver). É o que o seu monitoramento lê |
| `GET /api/painel.csv` | O painel em CSV |
| `GET /api/decisoes/exportar.csv` | Suas decisões, para a entrega das partes 2 e 3 |

O painel mostra **a visão do negócio**. Drift e análise de performance por segmento são seus, nos notebooks.

## Rodar e validar apenas o modelo exportado

Da raiz desta pasta, com Python 3.11 no Windows, crie um ambiente virtual e instale as dependências do modelo. Este caminho usa o pipeline salvo em disco e dispensa os serviços da aplicação.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r artefatos/parte1/modelo_exportado/requirements.txt
```

Na mesma pasta, execute a verificação abaixo. Ela pontua as 39.497 transações da referência, compara os scores com os valores salvos e recalcula o custo com o limiar da entrega.

```powershell
@"
import json
from pathlib import Path

import mlflow.sklearn
import numpy as np
import pandas as pd

evidencias = json.loads(Path("artefatos/parte1/evidencias_mlflow.json").read_text(encoding="utf-8"))
referencia = pd.read_csv("artefatos/parte1/referencia/validacao.csv")
modelo = mlflow.sklearn.load_model("artefatos/parte1/modelo_exportado")
entrada = referencia.loc[:, modelo.feature_names_in_]
scores = modelo.predict_proba(entrada)[:, 1]

assert len(referencia) == 39497
np.testing.assert_allclose(scores, referencia["score"], rtol=0, atol=5e-7)

bloquear = scores >= float(evidencias["tags_versao"]["threshold"])
fraude = referencia["fraude"].eq(1).to_numpy()
custo = round(
    referencia.loc[fraude & ~bloquear, "valor_transacao"].sum()
    + 15 * (~fraude & bloquear).sum(),
    2,
)
assert custo == evidencias["metricas"]["custo"], custo
print(f"Scores conferidos: {len(scores)} | custo: R$ {custo:.2f}")
"@ | .\.venv\Scripts\python.exe -
```

O resultado esperado é `Scores conferidos: 39497 | custo: R$ 28448.23`. Para verificar a integração do modelo com a API e o MLflow, use o procedimento da aplicação completa.
