"""Pré-processamento compartilhado pelo treino e pela inferência."""
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def preprocessador(contrato, escalar=False):
    categoricas = [f for f in contrato["features"] if f["tipo"] == "categoria"]
    numericas = [f["nome"] for f in contrato["features"] if f["tipo"] != "categoria"]
    return ColumnTransformer([
        ("categorias", OneHotEncoder(
            categories=[f["valores"] for f in categoricas],
            sparse_output=False,
        ), [f["nome"] for f in categoricas]),
        ("numeros", StandardScaler() if escalar else "passthrough", numericas),
    ])
