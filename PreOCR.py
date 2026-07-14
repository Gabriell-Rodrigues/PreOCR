# -*- coding: utf-8 -*-
"""
PreOCR - Deteccao de colunas, linhas e palavras em imagem PBM (P1).

Disciplina: Processamento de Imagens T01 2026.1 - Profa. Beatriz Trinchao Andrade
Grupo XX: (nomes dos integrantes)

===========================================================================
COMO USAR ESTE ARQUIVO (leia antes de comecar!)
===========================================================================
- Cada funcao esta marcada com [PESSOA 1/2/3/4] e o slide de referencia.
- Onde estiver "raise NotImplementedError(...)", quem for dono da funcao
  APAGA essa linha e escreve a implementacao no lugar.
- NAO mudem os NOMES nem os PARAMETROS das funcoes: e o "contrato" entre as
  partes. Se a Pessoa 3 vai chamar fechamento_horizontal(l, a, px, raio),
  esse nome tem que continuar igual.

CONTRATO DE DADOS (todo mundo usa o mesmo formato):
- Uma imagem e representada por (largura, altura, pixels).
- 'pixels' e uma LISTA de bytearrays: uma bytearray por linha da imagem,
  cada posicao com valor 0 (branco/fundo) ou 1 (preto/objeto/texto).
- Convencao das aulas (Morfologia I, slide 17): preto = 1, branco = 0.

ORDEM DE ENTREGA: Pessoa 1 -> Pessoa 2 -> Pessoa 3 -> Pessoa 4.
(Ninguem testa nada antes de a Pessoa 1 entregar ler_pbm/escrever_pbm.)

RESTRICAO DO TRABALHO: todas as funcoes sao implementadas pelo grupo.
Nao usar OpenCV, NumPy, Pillow etc. no PreOCR.py (so biblioteca padrao).
===========================================================================
"""

import sys
import os
from collections import deque


# ===========================================================================
# SECAO 1 - LEITURA/ESCRITA DE PBM E UTILIDADES        [PESSOA 1]
# ===========================================================================
 
def ler_pbm(caminho):
    """[PESSOA 1] Le um PBM ASCII (P1) e retorna (largura, altura, pixels).
 
    Passos:
      - abrir o arquivo (tratar erro de arquivo inexistente);
      - remover comentarios (tudo depois de '#' em cada linha);
      - separar em tokens; validar que o 1o token e 'P1';
      - ler largura e altura; validar que sao inteiros > 0;
      - ler os bits seguintes (podem vir colados '0101' ou separados);
      - validar que ha largura*altura pixels (senao arquivo truncado);
      - montar 'pixels' como lista de bytearrays (0/1).
 
    Deve lancar ValueError com mensagem clara em qualquer caso invalido
    (formato != P1, cabecalho incompleto, dimensoes invalidas, truncado,
    valor de pixel diferente de 0/1).  -> criterio: tratamento de erros
    """
    # Abrir o arquivo, e detectar erros de leitura
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            linhas = f.readlines()
    except FileNotFoundError:
        raise ValueError(f"Arquivo não encontrado: '{caminho}'")
    except IsADirectoryError:
        raise ValueError(f"Caminho é um diretorio, e não um arquivo: '{caminho}'")
    except UnicodeDecodeError as e:
        raise ValueError(
            f"Arquivo '{caminho}' não é um PBM ASCII valido "
            f"(Erro de codificação): {e}"
        )
    except OSError as e:
        raise ValueError(f"Não foi possivel abrir o arquivo '{caminho}': {e}")
 
    # --- Remover comentários #
    texto_sem_comentarios = []
    for linha in linhas:
        pos = linha.find('#')
        if pos != -1:
            linha = linha[:pos]
        texto_sem_comentarios.append(linha)
 
    # Separar em tokens
    tokens = ' '.join(texto_sem_comentarios).split()
 
    if len(tokens) < 1:
        raise ValueError(f"Arquivo '{caminho}' está vazio ou só tem comentários")
 
    # Validar numero mágico
    magico = tokens[0]
    if magico != 'P1':
        raise ValueError(
            f"formato invalido em '{caminho}': esperado 'P1', encontrado '{magico}'"
        )
 
    if len(tokens) < 3:
        raise ValueError(
            f"cabecalho PBM incompleto em '{caminho}': "
            f"esperado 'P1 largura altura'"
        )
 
    # Ler e validar largura/altura
    try:
        largura = int(tokens[1])
        altura = int(tokens[2])
    except ValueError:
        raise ValueError(
            f"largura/altura invalidas no cabecalho de '{caminho}' "
            f"(esperado numeros inteiros): '{tokens[1]}', '{tokens[2]}'"
        )
 
    if largura <= 0 or altura <= 0:
        raise ValueError(
            f"dimensoes invalidas em '{caminho}': "
            f"largura={largura}, altura={altura} (devem ser > 0)"
        )
 
    #-- Ler os bits seguintes (podem vir colados ou separados) --
    # Tokens[3:] pode ser algo como ['0','1','1',...] ou ['0101','1100',...]
    # ou uma mistura das duas coisas; juntamos tudo numa unica string de
    # digitos e depois consumimos exatamente largura*altura caracteres.
    bits = ''.join(tokens[3:])
 
    total_esperado = largura * altura
    if len(bits) < total_esperado:
        raise ValueError(
            f"arquivo '{caminho}' truncado: esperado {total_esperado} "
            f"pixels ({largura}x{altura}), encontrado {len(bits)}"
        )
 
    # Montar as listas de bitarrays com base nos 'pixels'
    pixels = []
    idx = 0
    for y in range(altura):
        linha_bits = bytearray(largura)
        for x in range(largura):
            c = bits[idx]
            idx += 1
            if c == '0':
                linha_bits[x] = 0
            elif c == '1':
                linha_bits[x] = 1
            else:
                raise ValueError(
                    f"Valor de pixel invalido '{c}' na posicão (x={x}, y={y}) "
                    f"de '{caminho}': esperado 0 ou 1"
                )
        pixels.append(linha_bits)
 
    return largura, altura, pixels
 
 
def escrever_pbm(caminho, largura, altura, pixels, comentario=None):
    """[PESSOA 1] Escreve a imagem em PBM ASCII (P1).
 
    Formato: linha 'P1', comentario opcional '# ...', 'largura altura',
    e depois uma linha de '0'/'1' por linha da imagem.
    """
    if largura <= 0 or altura <= 0:
        raise ValueError(
            f"Dimensões invalidas para escrita: largura={largura}, altura={altura}"
        )
    if len(pixels) != altura:
        raise ValueError(
            f"Número de linhas de 'pixels' ({len(pixels)}) não bate com "
            f"altura informada ({altura})"
        )
    for y, linha in enumerate(pixels):
        if len(linha) != largura:
            raise ValueError(
                f"Linha {y} de 'pixels' tem {len(linha)} colunas, "
                f"esperado largura={largura}"
            )
 
    try:
        with open(caminho, 'w', encoding='ascii') as f:
            f.write('P1\n')
            if comentario:
                for linha_comentario in str(comentario).splitlines():
                    f.write(f'# {linha_comentario}\n')
            f.write(f'{largura} {altura}\n')
            for linha in pixels:
                f.write(''.join('1' if v else '0' for v in linha))
                f.write('\n')
    except OSError as e:
        raise ValueError(f"Não foi possivel escrever o arquivo '{caminho}': {e}")
 
 
def copiar_imagem(pixels):
    """[PESSOA 1] Retorna uma copia independente de 'pixels'
    (lista de bytearrays novos, para nao alterar o original)."""
    return [bytearray(linha) for linha in pixels]


# ===========================================================================
# SECAO 2 - REMOCAO DE RUIDO (hit-or-miss)             [PESSOA 2]
# ===========================================================================
# Ruido "pimenta": pixel PRETO isolado -> transformada HIT-OR-MISS com
#   B1={origem} e B2=vizinhanca-8 (fundo). Remover = AFINAMENTO A-(A(*)B).
#   -> Morfologia I slides 52-55 ; Morfologia II slide 21 (afinamento)
# Ruido "sal": pixel BRANCO isolado dentro da letra -> caso DUAL
#   (ESPESSAMENTO A U (A(*)B)).  -> Morfologia II slide 26

def remover_ruido(largura, altura, pixels):
    """[PESSOA 2] Remove pixels pretos isolados e preenche buracos brancos
    isolados (hit-or-miss / afinamento / espessamento).

    Para cada pixel, olhar a vizinhanca-8:
      - se e 1 e TODOS os 8 vizinhos sao 0 -> vira 0 (pimenta);
      - se e 0 e TODOS os 8 vizinhos sao 1 -> vira 1 (sal).
    Retorna uma imagem nova (nao alterar a de entrada).
    """
    raise NotImplementedError("[PESSOA 2] implementar remover_ruido")


def erosao_2x2(largura, altura, pixels):
    """[PESSOA 2] EROSAO por elemento estruturante quadrado 2x2.
    Resultado[y][x] = 1 apenas se pixels[y][x], [y][x+1], [y+1][x],
    [y+1][x+1] forem todos 1. Serve de 'marcador' que sobrevive so dentro
    dos tracos das letras (>=2px), sumindo em aglomerados de ruido.
    -> Morfologia I slides 28-33 (erosao)
    """
    raise NotImplementedError("[PESSOA 2] implementar erosao_2x2")


def reconstruir_por_marcador(largura, altura, pixels, marcador):
    """[PESSOA 2] Mantem apenas os componentes conexos de 'pixels' que
    contem algum ponto do 'marcador' (o resto e ruido e vira 0).

    Dica: chamar componentes_conexos (Pessoa 3) para rotular; guardar num
    conjunto os rotulos que tem marcador; reconstruir so esses.
    E a reconstrucao morfologica (dilatacoes do marcador ∩ imagem), a mesma
    ideia da extracao de componentes conexos.  -> Morfologia II slides 17-19
    """
    raise NotImplementedError("[PESSOA 2] implementar reconstruir_por_marcador")


def filtrar_ruido_completo(largura, altura, pixels):
    """[PESSOA 2] Filtragem completa da Parte 1:
      1) remover_ruido  (pixels isolados e buracos de 1px)
      2) erosao_2x2     (gera o marcador)
      3) reconstruir_por_marcador (remove aglomerados de ruido)
    Retorna a imagem filtrada.
    """
    raise NotImplementedError("[PESSOA 2] implementar filtrar_ruido_completo")


# ===========================================================================
# SECAO 3 - MORFOLOGIA: DILATACAO, EROSAO, FECHAMENTO  [PESSOA 2]
# ===========================================================================
# Elementos estruturantes em RETA (1xk horizontal, kx1 vertical), origem no
# centro, raio = (k-1)/2.  Dilatacao/erosao 1D em tempo O(N) por linha.
#   Dilatacao:  A (+) B = { z | (B^)z ∩ A != vazio }   -> Morf I slide 22
#   Erosao:     A (-) B = { z | (B)z ⊆ A }             -> Morf I slide 28
#   Dualidade:  (A (-) B)^c = A^c (+) B^                -> Morf I slide 34
#   Fechamento: A . B = (A (+) B) (-) B                 -> Morf I slide 42

def _dilatar_linha(linha, raio, n):
    """[PESSOA 2] Dilatacao 1D de uma linha (bytearray): posicao vira 1 se
    existe algum 1 a distancia <= raio. Sugestao: duas varreduras medindo a
    distancia ao 1 mais proximo (esquerda->direita e direita->esquerda)."""
    raise NotImplementedError("[PESSOA 2] implementar _dilatar_linha")


def _erodir_linha(linha, raio, n):
    """[PESSOA 2] Erosao 1D. Pela dualidade (slide 34): complementa a linha,
    dilata e complementa de novo. Reaproveita _dilatar_linha."""
    raise NotImplementedError("[PESSOA 2] implementar _erodir_linha")


def _transpor(largura, altura, pixels):
    """[PESSOA 2] Transpoe a imagem (troca linhas por colunas). Usado para
    aplicar as operacoes 1D na vertical reaproveitando as horizontais."""
    raise NotImplementedError("[PESSOA 2] implementar _transpor")


def dilatacao_horizontal(largura, altura, pixels, raio):
    """[PESSOA 2] Dilata cada linha com _dilatar_linha."""
    raise NotImplementedError("[PESSOA 2] implementar dilatacao_horizontal")


def erosao_horizontal(largura, altura, pixels, raio):
    """[PESSOA 2] Erode cada linha com _erodir_linha."""
    raise NotImplementedError("[PESSOA 2] implementar erosao_horizontal")


def dilatacao_vertical(largura, altura, pixels, raio):
    """[PESSOA 2] Dilatacao vertical: transpor, dilatar linhas, transpor."""
    raise NotImplementedError("[PESSOA 2] implementar dilatacao_vertical")


def erosao_vertical(largura, altura, pixels, raio):
    """[PESSOA 2] Erosao vertical: transpor, erodir linhas, transpor."""
    raise NotImplementedError("[PESSOA 2] implementar erosao_vertical")


def fechamento_horizontal(largura, altura, pixels, raio):
    """[PESSOA 2] A . B = (A (+) B) (-) B com B = reta horizontal.
    Junta letras vizinhas sem juntar palavras. -> Morf I slide 42"""
    raise NotImplementedError("[PESSOA 2] implementar fechamento_horizontal")


def fechamento_vertical(largura, altura, pixels, raio):
    """[PESSOA 2] A . B = (A (+) B) (-) B com B = reta vertical.
    Usado para colar o pingo do 'i'/'j' ao corpo da palavra."""
    raise NotImplementedError("[PESSOA 2] implementar fechamento_vertical")


# ===========================================================================
# SECAO 4 - COMPONENTES CONEXOS                        [PESSOA 3]
# ===========================================================================

def componentes_conexos(largura, altura, pixels):
    """[PESSOA 3] Rotula os componentes conexos (vizinhanca-8) e retorna:
      - lista de caixas (ymin, xmin, ymax, xmax), uma por componente;
      - matriz 'rotulo' (mesmo tamanho da imagem) com o numero do
        componente de cada pixel (0 = fundo).

    E a extracao de componentes conexos da aula: a partir de um ponto
    semente P (X0=P), expande X_k = (X_{k-1} (+) B) ∩ A ate estabilizar.
    Implementar com uma fila (BFS), visitando cada pixel uma unica vez.
    -> Morfologia II slides 17-19 (formula no slide 18)
    """
    raise NotImplementedError("[PESSOA 3] implementar componentes_conexos")


# ===========================================================================
# SECAO 5 - TAMANHO DA LETRA                           [PESSOA 3]
# ===========================================================================

def mediana(valores):
    """[PESSOA 3] Mediana de uma lista de numeros (ordenar e pegar o meio)."""
    raise NotImplementedError("[PESSOA 3] implementar mediana")


def estimar_altura_letra(componentes):
    """[PESSOA 3] Estima a altura da letra = mediana das alturas das caixas
    dos componentes (descartar residuos minusculos, ex.: altura < 4).
    O enunciado garante letra com altura >= 12px. Os raios dos fechamentos
    sao calculados a partir desse valor, para funcionar em qualquer corpo."""
    raise NotImplementedError("[PESSOA 3] implementar estimar_altura_letra")


# ===========================================================================
# SECAO 6 - CAIXAS DAS PALAVRAS E DESENHO DOS RETANGULOS  [PESSOA 3]
# ===========================================================================

def caixas_reais(largura, altura, pixels_filtrados, rotulo_merged, n_comp):
    """[PESSOA 3] Para cada componente-palavra (rotulos da imagem 'fechada'),
    calcula a caixa delimitadora usando SO os pixels de texto originais
    (pixels_filtrados e subconjunto do fechamento). Retorna lista de caixas
    (ymin, xmin, ymax, xmax)."""
    raise NotImplementedError("[PESSOA 3] implementar caixas_reais")


def desenhar_retangulo(pixels, largura, altura, caixa, margem=2):
    """[PESSOA 3] Desenha (poe 1) as 4 bordas de um retangulo em volta da
    caixa (ymin,xmin,ymax,xmax), com uma pequena margem, sem estourar os
    limites da imagem."""
    raise NotImplementedError("[PESSOA 3] implementar desenhar_retangulo")


# ===========================================================================
# SECAO 7 - ORQUESTRACAO / MAIN            [PESSOA 3 conta, PESSOA 1 no main]
# ===========================================================================

def processar(caminho_entrada, verboso=True,
              fator_palavra=0.22, fator_linha=1.0):
    """Junta tudo. Esta montado como ROTEIRO com TODOs; conforme as funcoes
    forem ficando prontas, preencher cada passo.

    Passos previstos:
      1) largura, altura, imagem = ler_pbm(caminho_entrada)            [P1]
      2) filtrada = filtrar_ruido_completo(...)                        [P2]
         escrever_pbm(base + '_filtrada.pbm', ...)   # Parte 1         [P1/P2]
      3) h = estimar_altura_letra(componentes_conexos(filtrada))       [P3]
      4) PALAVRAS: W = fechamento_horizontal(filtrada, 0.22*h);        [P3]
         W = fechamento_vertical(W, 2);  # cola pingo do i
         comp_palavras, rotulo_W = componentes_conexos(W)
         n_palavras = len(comp_palavras)
      5) COLUNAS: L = fechamento_horizontal(W, 1.0*h);                 [P3]
         C = dilatacao_vertical(L, altura);   # une linhas da coluna
         n_colunas = len(componentes_conexos(C))
      6) LINHAS: para cada coluna, contar faixas horizontais de y com    [P3]
         texto dentro da mascara da coluna (interseccao). Linhas de
         colunas diferentes contam separadamente.
      7) desenhar retangulos em cada palavra e salvar _palavras.pbm    [P3]
      8) imprimir colunas / linhas / palavras                          [P3]

    Retorna (n_colunas, n_linhas, n_palavras).
    """
    raise NotImplementedError("[PESSOA 3] montar o processar seguindo o roteiro")


def main(argv):
    """[PESSOA 1] Interface de linha de comando.
      - se argumentos != 1 imagem -> imprimir modo de uso e sair;
      - chamar processar(caminho); capturar ValueError e imprimir 'Erro: ...'.
    Uso: python PreOCR.py <imagem.pbm>
    """
    if len(argv) != 2:
        print("Uso: python PreOCR.py <imagem.pbm>")
        return 1

    caminho = argv[1]

    try:
        processar(caminho)
    except ValueError as e:
        print(f"Erro: {e}")
        return 1
    
    return 0
    

if __name__ == '__main__':
    sys.exit(main(sys.argv))
