# Changelog — modelo antifraude

Uma entrada por versão que chegou (ou quase chegou) à produção, da mais nova para a mais antiga.
A versão aqui precisa bater com a descrição da versão no MLflow e, quando o contrato mudar, com o `contrato_features.yaml`.

Modelo de entrada:

```markdown
## vX.Y.Z — DD/MM/AAAA
- **Tipo:** modelo | pipeline | contrato
- **Versão no MLflow:** antifraude v<n>
- **O que mudou:**
- **Por quê:**
- **Evidência:** (run do MLflow, métrica, teste de drift)
- **Impacto:** (custo, taxa de bloqueio, recall — antes e depois)
- **Retreinou?** sim | não
```

---

<!-- Escreva a sua primeira entrada (v1.0.0) abaixo desta linha. -->

## v1.0.0 — 11/11/2026
- **Tipo:** modelo
- **Versão no MLflow:** antifraude v1
- **O que mudou:** Gradient boosting com pipeline das 13 features do contrato v1.0 e corte 0.05.
- **Por quê:** menor custo entre os modelos que superaram as três referências.
- **Evidência:** run `2325cc3ec53b4550b5cc074233906039`, referência em `referencia/` e teste de paridade da API no notebook.
- **Impacto:** nas semanas 11 e 12, custo de R$ 225.349,79 pela regra Pix para R$ 28.448,23, taxa de bloqueio de 0.63% para 2.70% e recall de 9.83% para 83.67%.
- **Retreinou?** sim, primeiro treino.
