# -*- coding: utf-8 -*-
"""
PreOCR - Contagem de colunas, linhas e palavras em imagem PBM ASCII (P1).

Disciplina: Processamento de Imagens T01 2026.1 - Profa. Beatriz Trinchao Andrade

Grupo G13:
    Evandro Jose dos Santos Neto
    Gabriel Rodrigues dos Santos
    Gustavo de Jesus Rodrigues
    Joao Felipe Tunes Oliveira

Uso: python3 PreOCR.py <imagem.pbm>

Saidas: numero de colunas, linhas e palavras no terminal, alem dos arquivos
<imagem>_filtrada.pbm (sem ruido) e <imagem>_palavras.pbm (palavras em retangulos).

Convencao: imagem = (largura, altura, pixels), onde pixels e uma lista de
bytearrays (uma por linha) com 1 = preto (texto) e 0 = branco (fundo).
"""

import sys
import os
from collections import deque


# Leitura e escrita de PBM ASCII (P1)

def ler_pbm(caminho):
    """Le um PBM ASCII (P1) e retorna (largura, altura, pixels)."""
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

    # Remove comentarios (tudo depois de '#')
    texto_sem_comentarios = []
    for linha in linhas:
        pos = linha.find('#')
        if pos != -1:
            linha = linha[:pos]
        texto_sem_comentarios.append(linha)

    tokens = ' '.join(texto_sem_comentarios).split()

    if len(tokens) < 1:
        raise ValueError(f"Arquivo '{caminho}' está vazio ou só tem comentários")

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

    # Os bits podem vir colados ('0101') ou separados ('0 1 0 1')
    bits = ''.join(tokens[3:])

    total_esperado = largura * altura
    if len(bits) < total_esperado:
        raise ValueError(
            f"arquivo '{caminho}' truncado: esperado {total_esperado} "
            f"pixels ({largura}x{altura}), encontrado {len(bits)}"
        )

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
    """Escreve a imagem em PBM ASCII (P1)."""
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
    """Retorna uma copia independente da imagem."""
    return [bytearray(linha) for linha in pixels]


# Remocao de ruido sal e pimenta (hit-or-miss + reconstrucao)

def remover_ruido(largura, altura, pixels):
    """Remove pixels pretos isolados e preenche buracos brancos de 1 px."""
    saida = copiar_imagem(pixels)
    viz = ((-1, -1), (-1, 0), (-1, 1), (0, -1),
           (0, 1), (1, -1), (1, 0), (1, 1))

    for y in range(altura):
        linha = pixels[y]
        for x in range(largura):
            if linha[x] == 1:
                # hit-or-miss: objeto na origem e fundo em toda a vizinhanca-8
                isolado = True
                for dy, dx in viz:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < altura and 0 <= nx < largura \
                            and pixels[ny][nx] == 1:
                        isolado = False
                        break
                if isolado:
                    saida[y][x] = 0
            else:
                # caso dual: fundo na origem cercado por objeto (buraco de 1 px)
                buraco = True
                for dy, dx in viz:
                    ny, nx = y + dy, x + dx
                    if not (0 <= ny < altura and 0 <= nx < largura) \
                            or pixels[ny][nx] == 0:
                        buraco = False
                        break
                if buraco:
                    saida[y][x] = 1
    return saida


def erosao_2x2(largura, altura, pixels):
    """Erosao por elemento estruturante quadrado 2x2 (marcador dos tracos)."""
    saida = [bytearray(largura) for _ in range(altura)]
    for y in range(altura - 1):
        l0, l1 = pixels[y], pixels[y + 1]
        s = saida[y]
        for x in range(largura - 1):
            if l0[x] and l0[x + 1] and l1[x] and l1[x + 1]:
                s[x] = 1
    return saida


def reconstruir_por_marcador(largura, altura, pixels, marcador):
    """Mantem so os componentes que contem marcador (Xk = (Xk-1 + B) inter A)."""
    saida = [bytearray(largura) for _ in range(altura)]
    fila = deque()

    # sementes: X0 = marcador intersecao imagem
    for y in range(altura):
        lm = marcador[y]
        lp = pixels[y]
        s = saida[y]
        for x in range(largura):
            if lm[x] and lp[x] and not s[x]:
                s[x] = 1
                fila.append((y, x))

    viz = ((-1, -1), (-1, 0), (-1, 1), (0, -1),
           (0, 1), (1, -1), (1, 0), (1, 1))

    # expande por dilatacoes sucessivas intersectadas com a imagem
    while fila:
        y, x = fila.popleft()
        for dy, dx in viz:
            ny, nx = y + dy, x + dx
            if 0 <= ny < altura and 0 <= nx < largura \
                    and pixels[ny][nx] == 1 and saida[ny][nx] == 0:
                saida[ny][nx] = 1
                fila.append((ny, nx))
    return saida


def filtrar_ruido_completo(largura, altura, pixels):
    """Filtragem completa: hit-or-miss + marcador 2x2 + reconstrucao."""
    filtrada = remover_ruido(largura, altura, pixels)
    marcador = erosao_2x2(largura, altura, filtrada)
    return reconstruir_por_marcador(largura, altura, filtrada, marcador)


# Dilatacao, erosao e fechamento com elementos estruturantes em reta

def _dilatar_linha(linha, raio, n):
    """Dilatacao 1D: vira 1 se ha algum 1 a distancia <= raio (duas varreduras)."""
    INF = n + 1
    dist = [INF] * n

    d = INF
    for i in range(n):
        d = 0 if linha[i] else (d + 1)
        dist[i] = d

    d = INF
    for i in range(n - 1, -1, -1):
        d = 0 if linha[i] else (d + 1)
        if d < dist[i]:
            dist[i] = d

    return bytearray(1 if dist[i] <= raio else 0 for i in range(n))


def _erodir_linha(linha, raio, n):
    """Erosao 1D: fica 1 so se todas as posicoes a distancia <= raio sao 1."""
    INF = n + 2
    dist = [INF] * n

    # fora da imagem conta como fundo (posicoes virtuais -1 e n)
    d = 0
    for i in range(n):
        d = 0 if linha[i] == 0 else (d + 1)
        dist[i] = d

    d = 0
    for i in range(n - 1, -1, -1):
        d = 0 if linha[i] == 0 else (d + 1)
        if d < dist[i]:
            dist[i] = d

    return bytearray(1 if dist[i] > raio else 0 for i in range(n))


def _transpor(largura, altura, pixels):
    """Transpoe a imagem (troca linhas por colunas)."""
    return [bytearray(pixels[y][x] for y in range(altura))
            for x in range(largura)]


def dilatacao_horizontal(largura, altura, pixels, raio):
    """Dilatacao com elemento estruturante reta horizontal 1x(2*raio+1)."""
    return [_dilatar_linha(pixels[y], raio, largura) for y in range(altura)]


def erosao_horizontal(largura, altura, pixels, raio):
    """Erosao com elemento estruturante reta horizontal 1x(2*raio+1)."""
    return [_erodir_linha(pixels[y], raio, largura) for y in range(altura)]


def dilatacao_vertical(largura, altura, pixels, raio):
    """Dilatacao com elemento estruturante reta vertical (2*raio+1)x1."""
    t = _transpor(largura, altura, pixels)
    t = [_dilatar_linha(t[x], raio, altura) for x in range(largura)]
    return _transpor(altura, largura, t)


def erosao_vertical(largura, altura, pixels, raio):
    """Erosao com elemento estruturante reta vertical (2*raio+1)x1."""
    t = _transpor(largura, altura, pixels)
    t = [_erodir_linha(t[x], raio, altura) for x in range(largura)]
    return _transpor(altura, largura, t)


def _fechar_linha(linha, raio, n):
    """Fechamento 1D com bordas estendidas para nao apagar pixels legitimos."""
    m = n + 2 * raio
    estendida = bytearray(raio) + linha + bytearray(raio)
    dil = _dilatar_linha(estendida, raio, m)
    ero = _erodir_linha(dil, raio, m)
    return ero[raio:raio + n]


def fechamento_horizontal(largura, altura, pixels, raio):
    """Fechamento A.B = (A dilatado) erodido, com B = reta horizontal."""
    return [_fechar_linha(pixels[y], raio, largura) for y in range(altura)]


def fechamento_vertical(largura, altura, pixels, raio):
    """Fechamento A.B = (A dilatado) erodido, com B = reta vertical."""
    t = _transpor(largura, altura, pixels)
    t = [_fechar_linha(t[x], raio, altura) for x in range(largura)]
    return _transpor(altura, largura, t)


# Extracao de componentes conexos

def componentes_conexos(largura, altura, pixels):
    """Rotula componentes conexos (vizinhanca-8); retorna (caixas, rotulos)."""
    rotulo = [[0] * largura for _ in range(altura)]
    componentes = []
    atual = 0
    viz = ((-1, -1), (-1, 0), (-1, 1), (0, -1),
           (0, 1), (1, -1), (1, 0), (1, 1))

    for y0 in range(altura):
        linha0 = pixels[y0]
        for x0 in range(largura):
            if linha0[x0] == 1 and rotulo[y0][x0] == 0:
                # expande a partir do ponto semente: Xk = (Xk-1 + B) inter A
                atual += 1
                ymin = ymax = y0
                xmin = xmax = x0
                fila = deque([(y0, x0)])
                rotulo[y0][x0] = atual
                while fila:
                    y, x = fila.popleft()
                    if y < ymin: ymin = y
                    if y > ymax: ymax = y
                    if x < xmin: xmin = x
                    if x > xmax: xmax = x
                    for dy, dx in viz:
                        ny, nx = y + dy, x + dx
                        if (0 <= ny < altura and 0 <= nx < largura
                                and pixels[ny][nx] == 1
                                and rotulo[ny][nx] == 0):
                            rotulo[ny][nx] = atual
                            fila.append((ny, nx))
                componentes.append((ymin, xmin, ymax, xmax))
    return componentes, rotulo


# Estimativa do tamanho da letra

def mediana(valores):
    """Mediana de uma lista de numeros."""
    v = sorted(valores)
    n = len(v)
    if n == 0:
        return 0
    if n % 2 == 1:
        return v[n // 2]
    return (v[n // 2 - 1] + v[n // 2]) / 2.0


def estimar_altura_letra(componentes):
    """Estima a altura da letra pela mediana das alturas dos componentes."""
    alturas = []
    for (ymin, xmin, ymax, xmax) in componentes:
        h = ymax - ymin + 1
        if h >= 4:
            alturas.append(h)
    if not alturas:
        return 0
    return mediana(alturas)


# Caixas das palavras e desenho dos retangulos

def caixas_reais(largura, altura, pixels_filtrados, rotulo_merged, n_comp):
    """Caixa delimitadora de cada palavra usando so os pixels de texto."""
    caixas = {}
    for y in range(altura):
        linha = pixels_filtrados[y]
        lrot = rotulo_merged[y]
        for x in range(largura):
            if linha[x] == 1:
                r = lrot[x]
                if r == 0:
                    continue
                if r in caixas:
                    ymin, xmin, ymax, xmax = caixas[r]
                    caixas[r] = (min(ymin, y), min(xmin, x),
                                 max(ymax, y), max(xmax, x))
                else:
                    caixas[r] = (y, x, y, x)
    return list(caixas.values())


def desenhar_retangulo(pixels, largura, altura, caixa, margem=2):
    """Desenha as 4 bordas de um retangulo em volta da caixa, com margem."""
    ymin, xmin, ymax, xmax = caixa
    y1 = max(0, ymin - margem)
    x1 = max(0, xmin - margem)
    y2 = min(altura - 1, ymax + margem)
    x2 = min(largura - 1, xmax + margem)
    for x in range(x1, x2 + 1):
        pixels[y1][x] = 1
        pixels[y2][x] = 1
    for y in range(y1, y2 + 1):
        pixels[y][x1] = 1
        pixels[y][x2] = 1


# Programa principal

def processar(caminho_entrada, verboso=True,
              fator_palavra=0.22, fator_linha=1.0):
    """Executa o pipeline completo e retorna (colunas, linhas, palavras)."""
    largura, altura, imagem = ler_pbm(caminho_entrada)

    # Parte 1: remove o ruido e salva a imagem filtrada
    filtrada = filtrar_ruido_completo(largura, altura, imagem)
    base, _ = os.path.splitext(caminho_entrada)
    escrever_pbm(base + '_filtrada.pbm', largura, altura, filtrada,
                 'imagem filtrada (ruido sal e pimenta removido)')

    # estima o tamanho da letra a partir dos componentes (letras)
    letras, _ = componentes_conexos(largura, altura, filtrada)
    h = estimar_altura_letra(letras)
    if h == 0:
        if verboso:
            print('colunas: 0')
            print('linhas: 0')
            print('palavras: 0')
        escrever_pbm(base + '_palavras.pbm', largura, altura, filtrada,
                     'nenhuma palavra encontrada')
        return 0, 0, 0

    # palavras: fechamento horizontal une letras; vertical cola o pingo do i
    raio_palavra = max(1, int(round(fator_palavra * h)))
    W = fechamento_horizontal(largura, altura, filtrada, raio_palavra)
    W = fechamento_vertical(largura, altura, W, 2)
    comp_palavras, rotulo_W = componentes_conexos(largura, altura, W)
    n_palavras = len(comp_palavras)

    # colunas: fechamento maior une as palavras de cada linha, e a dilatacao
    # vertical (puramente vertical, nunca une colunas) funde as linhas
    raio_linha = max(raio_palavra + 1, int(round(fator_linha * h)))
    L = fechamento_horizontal(largura, altura, W, raio_linha)
    C = dilatacao_vertical(largura, altura, L, altura)
    comp_colunas, _ = componentes_conexos(largura, altura, C)
    n_colunas = len(comp_colunas)

    # linhas: faixas de y com texto dentro da faixa x de cada coluna
    n_linhas = 0
    for (cy1, cx1, cy2, cx2) in comp_colunas:
        dentro_de_linha = False
        for y in range(altura):
            linha_y = W[y]
            tem_texto = False
            for x in range(cx1, cx2 + 1):
                if linha_y[x]:
                    tem_texto = True
                    break
            if tem_texto and not dentro_de_linha:
                n_linhas += 1
                dentro_de_linha = True
            elif not tem_texto:
                dentro_de_linha = False

    # desenha um retangulo em volta de cada palavra e salva a saida
    saida = copiar_imagem(filtrada)
    for caixa in caixas_reais(largura, altura, filtrada, rotulo_W, n_palavras):
        desenhar_retangulo(saida, largura, altura, caixa)
    escrever_pbm(base + '_palavras.pbm', largura, altura, saida,
                 'palavras circunscritas por retangulos')

    if verboso:
        print(f'colunas: {n_colunas}')
        print(f'linhas: {n_linhas}')
        print(f'palavras: {n_palavras}')
    return n_colunas, n_linhas, n_palavras


def main(argv):
    """Interface de linha de comando: python PreOCR.py <imagem.pbm>."""
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
