"""Custo, drift e desempenho de lotes pontuados."""
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, ks_2samp
from sklearn.metrics import average_precision_score, precision_score, recall_score

from config import CUSTO_FALSO_POSITIVO


def custo(fraude, valor, bloquear):
    fraude = np.asarray(fraude, dtype=bool)
    bloquear = np.asarray(bloquear, dtype=bool)
    return round(float(np.asarray(valor)[fraude & ~bloquear].sum())
                 + CUSTO_FALSO_POSITIVO * int((~fraude & bloquear).sum()), 2)


def drift(referencia, lote, contrato):
    resultados = []
    for feature in [*contrato["features"], {"nome": "score", "tipo": "float"}]:
        nome = feature["nome"]
        antes, depois = referencia[nome].dropna(), lote[nome].dropna()
        discreta = (feature["tipo"] in ("categoria", "bool")
                    or nome in ("hora_transacao", "dia_semana"))
        efeito = p = np.nan
        teste = "qui-quadrado" if discreta else "KS"
        if len(antes) and len(depois):
            if discreta:
                contagens = pd.concat([antes.value_counts(), depois.value_counts()],
                                      axis=1).fillna(0)
                proporcoes = contagens / contagens.sum()
                efeito = (proporcoes.iloc[:, 0] - proporcoes.iloc[:, 1]).abs().sum() / 2
                p = chi2_contingency(contagens, correction=False).pvalue
            else:
                efeito, p = ks_2samp(antes, depois)
        resultados.append({"feature": nome, "teste": teste, "efeito": efeito,
                           "p_valor": p, "alerta": bool(efeito > 0.10 and p < 0.01)})
    return pd.DataFrame(resultados)


def saida(lote, threshold):
    pontuadas = lote.dropna(subset=["score"])
    bloqueadas = pontuadas["score"] >= threshold
    return pd.DataFrame([{
        "pontuadas": len(pontuadas),
        "taxa_bloqueio": bloqueadas.mean(),
        "valor_bloqueado": pontuadas.loc[bloqueadas, "valor_transacao"].sum(),
    }])


def desempenho(lote, threshold, segmento="canal"):
    if "fraude" not in lote:
        return pd.DataFrame()
    rotuladas = lote.dropna(subset=["fraude", "score"])
    resultados = []
    for nome, grupo in [("total", rotuladas), *rotuladas.groupby(segmento)]:
        if grupo.empty:
            continue
        fraude = grupo["fraude"].astype(int)
        bloqueadas = grupo["score"] >= threshold
        resultados.append({
            "segmento": nome, "transacoes": len(grupo), "fraudes": int(fraude.sum()),
            "recall": recall_score(fraude, bloqueadas, zero_division=0),
            "precision": precision_score(fraude, bloqueadas, zero_division=0),
            "pr_auc": average_precision_score(fraude, grupo["score"]) if fraude.any() else np.nan,
            "custo": custo(fraude, grupo["valor_transacao"], bloqueadas),
            "legitimas_bloqueadas": int(((fraude == 0) & bloqueadas).sum()),
            "fraudes_aprovadas": int(((fraude == 1) & ~bloqueadas).sum()),
            "valor_fraude_aprovada": grupo.loc[(fraude == 1) & ~bloqueadas, "valor_transacao"].sum(),
        })
    return pd.DataFrame(resultados)
