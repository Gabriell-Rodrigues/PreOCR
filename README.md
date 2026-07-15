# PreOCR

Trabalho prático de **Processamento de Imagens (T01 2026.1)** — Profa. Beatriz Trinchão Andrade — UFS.

Programa que recebe uma imagem binária **PBM ASCII (P1)** contendo texto em
Arial e retorna no terminal o número de **colunas, linhas e palavras**, além
de gerar uma imagem PBM com cada palavra circunscrita por um retângulo.
Técnicas: morfologia matemática (hit-or-miss, dilatação, erosão, fechamento
e extração de componentes conexos).

## Uso

```bash
python3 PreOCR.py <imagem.pbm>
```

Saída no terminal:

```
colunas: 2
linhas: 99
palavras: 583
```

Arquivos gerados: `<imagem>_filtrada.pbm` (ruído removido — Parte 1) e
`<imagem>_palavras.pbm` (palavras circunscritas — Parte 2).

Sem dependências externas: apenas a biblioteca padrão do Python (≥ 3.6).
Todas as funções foram implementadas pelo grupo.

## Estrutura

| Item | Descrição |
|---|---|
| `PreOCR.py` | Programa completo |
| `base_teste/` | Imagens de teste da disciplina (10 `.pbm`) e gabaritos (`.odt`) |
| `imagens_grupo/` | As 3 imagens de teste de autoria do grupo |
| `relatorio.md` | Relatório do trabalho |

## Divisão do grupo

| Pessoa | Responsável por |
|---|---|
| **1** | Leitura/escrita PBM, validação de erros, linha de comando |
| **2** | Remoção de ruído (hit-or-miss) e operações morfológicas |
| **3** | Componentes conexos, contagem palavras/linhas/colunas, retângulos |
| **4** | Bateria de testes, gabarito, figuras e relatório |
