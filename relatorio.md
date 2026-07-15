# PreOCR — Detecção de colunas, linhas e palavras em imagens PBM

**Disciplina:** Processamento de Imagens — T01 2026.1 — Profa. Beatriz Trinchão Andrade
**Grupo XX:** _(nomes dos integrantes)_

---

## 1. O que foi feito

Foi desenvolvido, em Python (sem nenhuma biblioteca externa — todas as
funções foram implementadas pelo grupo), um programa que recebe pela linha
de comando uma imagem binária no formato PBM ASCII (P1) contendo texto em
Arial e:

1. **Remove o ruído sal e pimenta** (tamanho de 1 pixel) e salva a imagem
   filtrada em `entrada_filtrada.pbm` (Parte 1);
2. **Conta e imprime no terminal** o número de **colunas**, **linhas** e
   **palavras** do texto (linhas de colunas diferentes contam
   separadamente);
3. **Gera** `entrada_palavras.pbm`, com cada palavra circunscrita por um
   retângulo (Parte 2).

Também foram criadas três imagens de teste de autoria do grupo (pasta
`imagens_grupo/`), nomeadas no formato exigido
`grupo_XX_imagem_N_linhas_Y_palavras_Z.pbm`.

## 2. Técnicas da disciplina aplicadas e parâmetros

Todas as etapas usam exclusivamente operações vistas nas aulas de
**Morfologia Matemática I e II** (a imagem é tratada como conjunto A ⊂ Z²;
convenção: preto = 1 = objeto).

| Etapa | Técnica da aula | Parâmetros |
|---|---|---|
| Ruído (pixels isolados) | **Transformada hit-or-miss** + **afinamento** A ⊗ B = A − (A ⊛ B), com B1 = {origem} e B2 = vizinhança-8; buracos de 1 px pelo caso dual (**espessamento**) | elemento 3×3 |
| Ruído (aglomerados) | **Erosão** por quadrado 2×2 gera um *marcador* (só sobrevive dentro dos traços das letras, que têm espessura ≥ 2 px); em seguida, **extração de componentes conexos a partir de sementes** — X_k = (X_{k−1} ⊕ B) ∩ A — mantém apenas os componentes que contêm marcador | SE 2×2 |
| Tamanho da letra | **Extração de componentes conexos** (vizinhança-8) e mediana das alturas das caixas | h ≈ 18 px na base de teste |
| Palavras | **Fechamento** A • B = (A ⊕ B) ⊖ B com SE reta horizontal (une letras, pois o espaço entre letras ≪ espaço entre palavras) + fechamento com SE reta vertical (une o pingo de i/j ao corpo — vão medido: 3 px) | raio horizontal = 0,22·h; raio vertical = 2 |
| Colunas | Fechamento horizontal maior (une palavras de uma linha sem atravessar o corredor entre colunas) + **dilatação vertical** com SE da altura da imagem: como a dilatação é puramente vertical, colunas distintas nunca se unem | raio linha = 1,0·h |
| Linhas | **Dilatação horizontal** + **interseção** com a máscara da coluna (operadores lógicos/teoria dos conjuntos): cada linha do texto vira uma faixa conexa dentro da coluna; contam-se os componentes | — |
| Retângulos | Caixa delimitadora dos pixels do texto dentro de cada componente-palavra (o texto filtrado é subconjunto do fechamento — propriedade do fechamento vista em aula) | margem de 2 px |

Os raios são **relativos à altura mediana da letra (h)**, estimada da
própria imagem — o programa funciona portanto para qualquer corpo de fonte
(≥ 12 px, como garante o enunciado), sem parâmetros fixos em pixels.

## 3. Principais problemas e soluções

* **Pingos de "i"/"j" e pontuação viravam "palavras" separadas** (368
  componentes de altura 3 na base de teste). Solução: medimos o vão
  vertical pingo→corpo (3 px) e aplicamos um fechamento vertical de raio 2
  após o fechamento horizontal — o pingo se une à palavra sem alcançar a
  linha vizinha.
* **Ruído denso forma pares/trincas de pixels** que o hit-or-miss de pixel
  isolado não remove (1.315 aglomerados restantes em `lorem_s12_c03_noise`).
  Solução: marcador por erosão 2×2 + reconstrução por componentes conexos.
  Verificamos que **nenhum** componente legítimo da base de teste é perdido
  (todo traço de letra contém um bloco 2×2). Uma **abertura** também
  removeria o ruído, mas danificaria os traços finos das letras (~2 px).
* **Espaços esticados do texto justificado** quebravam a contagem de
  linhas, e **espaços vazios** (variante `_espacos`) dividiam uma coluna em
  vários blocos. Solução: contar colunas com dilatação puramente vertical
  (insensível a vãos verticais) e contar linhas por faixas horizontais
  dentro da máscara de cada coluna (insensível ao espaçamento horizontal).
* **Bordas nas operações morfológicas**: pela dualidade
  (A ⊖ B)ᶜ = Aᶜ ⊕ B̂, o complemento de A em Z² é infinito, então fora da
  imagem conta como fundo na erosão; no fechamento, a dilatação intermediária
  é calculada com o domínio estendido para não violar a propriedade
  A ⊆ A • B.
* **Eficiência**: dilatação/erosão 1D implementadas em tempo O(N) por
  varredura dupla (distância ao objeto mais próximo), independente do raio;
  componentes conexos com fila (cada pixel visitado uma única vez) — é a
  realização eficiente da definição iterativa X_k = (X_{k−1} ⊕ B) ∩ A da
  aula. Uma página A4 (1653×2338) é processada em ~10–15 s em Python puro.

## 4. Resultados

Contagens nas 10 imagens da base de teste (gabarito de palavras extraído
dos arquivos `.odt` correspondentes — contagens exatas em todas):

| Imagem | Colunas | Linhas | Palavras |
|---|---|---|---|
| lorem_s12_c02 (e _noise) | 2 ✓ | 99 | 583 ✓ |
| lorem_s12_c02_espacos (e _noise) | 2 ✓ | 81 | 476 ✓ |
| lorem_s12_c02_just (e _noise) | 2 ✓ | 99 | 583 ✓ |
| lorem_s12_c03 (e _noise) | 3 ✓ | 150 | 557 ✓ |
| lorem_s12_c03_just (e _noise) | 3 ✓ | 150 | 557 ✓ |

O texto justificado tem exatamente as mesmas quebras de linha do não
justificado (99 = 99; 150 = 150), o que confirma a contagem de linhas. As
três imagens do grupo também retornam exatamente os valores dos nomes dos
arquivos (1/13/108, 2/38/170 e 3/61/223).

_(Inserir aqui as figuras: recorte da imagem com ruído, da filtrada e da
saída com os retângulos.)_

## 5. Tratamento de erros

O programa rejeita com mensagem clara: arquivo inexistente, formato
diferente de P1, cabeçalho incompleto, dimensões inválidas, arquivo
truncado e valores de pixel diferentes de 0/1. Imagem sem texto retorna
0 colunas, 0 linhas, 0 palavras.

## 6. Compilação e execução no Linux

Não há compilação (Python ≥ 3.6, apenas biblioteca padrão):

```bash
python3 PreOCR.py lorem_s12_c02.pbm
```

Saída no terminal:

```
colunas: 2
linhas: 99
palavras: 583
```

Arquivos gerados no mesmo diretório da entrada:
`lorem_s12_c02_filtrada.pbm` e `lorem_s12_c02_palavras.pbm`.
