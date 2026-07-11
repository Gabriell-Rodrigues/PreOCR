# PreOCR

Trabalho de **Processamento de Imagens (T01 2026.1)** — Profa. Beatriz Trinchão Andrade.

Programa que recebe uma imagem binária **PBM ASCII (P1)** contendo texto em
Arial e retorna no terminal o número de **colunas, linhas e palavras**, além
de gerar uma imagem PBM com cada palavra circunscrita por um retângulo.
Baseado nas aulas de **Morfologia Matemática I e II**.

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

Arquivos gerados: `<imagem>_filtrada.pbm` (Parte 1) e
`<imagem>_palavras.pbm` (Parte 2).

> Sem dependências externas: apenas a biblioteca padrão do Python (≥ 3.6).
> Todas as funções são implementadas pelo grupo.

## Divisão do grupo

| Pessoa | Responsável por | Seções em `PreOCR.py` |
|---|---|---|
| **1** | Leitura/escrita PBM, validação de erros, linha de comando | 1 e 7 (`main`) |
| **2** | Remoção de ruído (hit-or-miss) e operações morfológicas (dilatação, erosão, fechamento) | 2 e 3 |
| **3** | Componentes conexos, contagem palavras/linhas/colunas, retângulos, `processar` | 4, 5, 6, 7 |
| **4** | Bateria de testes, gabarito, figuras e relatório | — |

## Como colaborar (importante)

- Cada um implementa **apenas as funções da sua seção**, marcadas com
  `[PESSOA X]`. Onde houver `raise NotImplementedError(...)`, apague a linha
  e escreva o código.
- **Não mudem os nomes nem os parâmetros das funções** — é o contrato entre
  as partes.
- **Contrato de dados:** a imagem é `(largura, altura, pixels)`, onde
  `pixels` é uma lista de `bytearray` (uma por linha) com valores 0/1
  (preto = 1, branco = 0).
- Ordem de entrega: **P1 → P2 → P3 → P4** (ninguém testa antes de a
  Pessoa 1 entregar a leitura de PBM).

## Fluxo Git sugerido

```bash
git pull                 # sempre antes de começar a mexer
# ... implementa sua secao ...
git add PreOCR.py
git commit -m "Pessoa X: implementa <funcoes>"
git push
```

Evitem duas pessoas editando a mesma seção ao mesmo tempo.
