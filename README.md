# Banco Aurora — Projeto antifraude

O Banco Aurora usa um modelo para decidir quais transações Pix e de cartão bloquear. O custo de uma decisão é a soma do valor das fraudes aprovadas com R$ 15 por transação legítima bloqueada. O sistema bloqueia quando o score de fraude é maior ou igual ao limiar escolhido na validação.

Na Parte 1, a regressão logística e o Gradient Boosting foram treinados nas semanas 1 a 10 e avaliados nas semanas 11 e 12. O Gradient Boosting, com limiar de 0,05, foi registrado no MLflow como `antifraude@champion`. Seu custo na validação foi de R$ 28.448,23, frente a R$ 225.349,79 da regra de bloquear Pix acima de R$ 1.000. O modelo identificou 502 das 600 fraudes e bloqueou 563 transações legítimas.

## Arquivos da Parte 1

| Arquivo | Conteúdo |
| --- | --- |
| [parte1.ipynb](parte1.ipynb) | Validação dos dados, treino, escolha do limiar, registro no MLflow e teste com a API. |
| [contrato_features.yaml](contrato_features.yaml) e [features.py](features.py) | Contrato das 13 variáveis e pré-processamento usado no pipeline. |
| [monitoramento.py](monitoramento.py) | Custo, drift, bloqueios e desempenho global e por canal. |
| [referencia/validacao.csv](referencia/validacao.csv) | Variáveis, scores e rótulos das semanas 11 e 12. |
| [modelo_exportado](modelo_exportado), [evidencias_mlflow.json](evidencias_mlflow.json) e [CHANGELOG.md](CHANGELOG.md) | Pipeline exportado, metadados da execução e histórico de versões. |

## Rodar a aplicação completa

Esta pasta contém os artefatos da Parte 1. Para iniciar a aplicação original e reexecutar o notebook, obtenha a pasta-base do exercício, com o código da API em `app/`, o `config.py`, os dados históricos em `dados/` e as instruções de inicialização dos serviços.

1. Siga o README da pasta-base para iniciar o PostgreSQL, o MLflow e a API. O notebook usa `config.py` para localizar os bancos da aplicação e do MLflow e as URLs dos serviços.
2. Na raiz da pasta-base, disponibilize os arquivos da Parte 1. Confira os caminhos que o notebook e a API usam para localizar o contrato e os CSVs `dados/transacoes_semanas_01_12.csv` e `dados/rotulos_semanas_01_12.csv`.
3. Abra `parte1.ipynb` com o ambiente Python da aplicação e execute a seção **0. Ambiente**. As quatro verificações devem passar. Em um ambiente novo, o alias `champion` aparece depois do registro do modelo.
4. Para reconstruir a Parte 1, execute as células do notebook em ordem. A etapa de registro cria uma versão no MLflow e aponta o alias `champion` para ela.

### Validar a aplicação

Com as portas registradas no notebook, execute no PowerShell. Se a configuração local usar outras portas, ajuste as URLs.

```powershell
Invoke-WebRequest http://127.0.0.1:5000/health
Invoke-RestMethod http://127.0.0.1:8000/saude | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8000/modelo | ConvertTo-Json -Depth 5
```

- O MLflow deve responder com HTTP 200. A API deve indicar sistema saudável e, após o registro, modelo disponível com contrato 1.0 e limiar 0,05. A entrega original registrou a versão 1. Em uma reexecução, confira se a versão exibida coincide com o alias atual.
- No MLflow, confira se `antifraude@champion` aponta para a versão esperada, se a versão tem as tags `threshold` e `motivo` e se a execução contém o artefato `referencia/validacao.csv`.
- Execute a seção **8. O sistema está usando o seu modelo?**. Ela envia cinco transações da semana 12 a `POST /predict` e compara scores, decisões e versão com o modelo carregado do MLflow. As verificações devem passar.
- Execute a seção **9. Monitoramento baseline**. A comparação das semanas 11 e 12 deve terminar sem alertas. O critério exige efeito acima de 0,10 e p-valor abaixo de 0,01.

## Rodar e validar apenas o modelo exportado

Da raiz desta pasta, com Python 3.11 no Windows, crie um ambiente virtual e instale as dependências do modelo. Este caminho usa o pipeline salvo em disco e dispensa os serviços da aplicação.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r modelo_exportado/requirements.txt
```

Na mesma pasta, execute a verificação abaixo. Ela pontua as 39.497 transações da referência, compara os scores com os valores salvos e recalcula o custo com o limiar da entrega.

```powershell
@"
import json
from pathlib import Path

import mlflow.sklearn
import numpy as np
import pandas as pd

evidencias = json.loads(Path("evidencias_mlflow.json").read_text(encoding="utf-8"))
referencia = pd.read_csv("referencia/validacao.csv")
modelo = mlflow.sklearn.load_model("modelo_exportado")
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
