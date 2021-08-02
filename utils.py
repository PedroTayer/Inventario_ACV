import math

import numpy as np
import pandas as pd


def calcular_inventario(A, B, k):
    inva = np.linalg.inv(A.to_numpy())
    s = np.matmul(inva, k.to_numpy())
    g = np.matmul(B.to_numpy(), s)
    mlambda = np.matmul(B.to_numpy(), inva)

    dfs = pd.DataFrame(data=s[0:, 0:],
                       index=[i for i in range(s.shape[0])],
                       columns=['Column' + str(i) for i in range(s.shape[1])])

    dfg = pd.DataFrame(data=g[0:, 0:],
                       index=[i for i in range(g.shape[0])],
                       columns=['Emissão' for i in range(g.shape[1])])

    dflambda = pd.DataFrame(data=mlambda[0:, 0:],
                            index=[i for i in range(mlambda.shape[0])],
                            columns=['Column' + str(i) for i in range(mlambda.shape[1])])

    dict_map_index = {ind: val for ind, val in enumerate(B.index.to_list())}
    dfg.rename(dict_map_index, inplace=True)

    return dfs, dfg, dflambda, inva


def coluna_fantasma(A, B, k, nprocessos):
    dfa = A.copy()
    dfb = B.copy()
    dfk = k.copy()

    fantasma = f'P{nprocessos + 1}'
    dfa[fantasma] = 0
    dfa.loc[dfa.index[-1], fantasma] = 1
    dfb[fantasma] = 0

    return dfa, dfb, dfk

def criterio_de_corte(A, B, k, produto):
    # Retirar o produto do A e do k e colocar como um B
    dfa = A[A.index!=produto]
    dfk = k[k.index!=produto]

    dfb = B.copy()
    try:
        dfb = dfb.append(A.loc[[produto]])
    except KeyError:
        print(f'{produto} não encontrado na matriz.')
        return None, None, None
    
    return dfa, dfb, dfk


def alocar(A, B, k, nprocessos, processo, produto1, produto2):

    dfa = A.copy()
    dfb = B.copy()
    dfk = k.copy()

    # Dividir um processo em 2 subprocessos e alocar por massa
    processo_a_ser_dividido = f'P{processo}'
    processo_a_ser_criado = f'P{nprocessos+1}'

    # Vamos dividir o processo 2 em aço e ferro fundido
    # O novo processo 2 vai ter tudo de aço, 0 de fofo, e a proporção entre aço e fofo do antigo processo 2 para os outros produtos
    # O novo processo 3 vai ter 0 de aço, tudo de fofo, e a proporção entre aço e fofo do antigo processo 2 para os outros produtos

    qtd_el1 = dfa.loc[produto1, processo_a_ser_dividido]
    qtd_el2 = dfa.loc[produto2, processo_a_ser_dividido]
    tot = qtd_el1 + qtd_el2

    prop_el1 = qtd_el1 / tot
    prop_el2 = qtd_el2 / tot

    dfa[processo_a_ser_criado] = dfa[processo_a_ser_dividido] * prop_el2  # vai ser do fofo
    dfa.at[produto1, processo_a_ser_criado] = 0
    dfa.at[produto2, processo_a_ser_criado] = qtd_el2

    dfa[processo_a_ser_dividido] = dfa[processo_a_ser_dividido] * prop_el1  # vai ser do aço
    dfa.at[produto1, processo_a_ser_dividido] = qtd_el1
    dfa.at[produto2, processo_a_ser_dividido] = 0

    dfb[processo_a_ser_criado] = dfb[processo_a_ser_dividido] * prop_el2  # vai ser do aço
    dfb[processo_a_ser_dividido] = dfb[processo_a_ser_dividido] * prop_el1  # vai ser do aço

    return dfa, dfb, dfk


def ler_entradas(filename):
    # Ler o excel
    filename = 'entradas.xlsx'  # atribui o arquivo em excel na variável
    df = pd.read_excel(filename, sheet_name='processos')  # lê a planilha 'processos' do arquivo em excel
    df.fillna(0, inplace=True)  # todos os valores nulos serão substituídos por zero

    colsprocessos = [i for i in df.columns if i.startswith('Processo')]
    nprocessos = len(colsprocessos)

    colsstd_processos = ['std P' + str(p + 1) for p in range(nprocessos)]

    colsq = [i for i in df.columns if i.startswith('Q')]
    nqs = len(colsq)

    colsq_processos = ['std Q' + str(q + 1) for q in range(nqs)]

    dtipos_stdp = pd.Series(df.stdP.values, index=df.Produto).to_dict()

    colsq_tipos = [f'stdQ{q + 1}-Tipo' for q in range(nqs)]
    dtipos_stdq = {}
    for q in range(len(df[colsq_tipos].iloc[0])):
        dtipos_stdq[f'{q + 1}'] = df[colsq_tipos].iloc[0][q]

    # Matriz A é com intermediário=1
    dfA = df[df['Intermediário'] == 1][['Produto'] + colsprocessos].copy()
    dfA.set_index('Produto', inplace=True)

    # Matriz B é com intermediário=0
    dfB = df[df['Intermediário'] == 0][['Produto'] + colsprocessos].copy()
    dfB.set_index('Produto', inplace=True)

    # Matriz k é o fluxo de referência
    dfk = df[df['Intermediário'] == 1][['Produto', 'Fluxo de referência']].copy()
    dfk.set_index('Produto', inplace=True)

    # Calcular novas matrizes pelo critério de corte (deixar quadrada), função escrita em utils
    dfa, dfb, dfk = criterio_de_corte(dfA, dfB, dfk, 'fofo')
    stda = df[df['Produto'].isin(dfa.index.tolist())][['Produto'] + colsstd_processos].copy()
    stda.set_index('Produto', inplace=True)

    stdb = df[df['Produto'].isin(dfb.index.tolist())][['Produto'] + colsstd_processos].copy()
    stdb.set_index('Produto', inplace=True)

    dfq = df[df['Produto'].isin(dfb.index.tolist())][['Produto'] + colsq].copy()
    dfq = dfq.set_index('Produto').T

    stdq = df[df['Produto'].isin(dfb.index.tolist())][['Produto'] + colsq_processos].copy()
    stdq = stdq.set_index('Produto').T

    return dfa, dfb, dfk, dfq, stda, stdb, stdq, dtipos_stdp, dtipos_stdq


def calcular_variancias(media, desvio, dftipo, dfmedia, matrizq=False):
    dict_tipos = {'normal': 1, 'lognormal': 2}
    tipo_std = np.zeros(media.shape)

    for i in range(media.shape[0]):
        for j in range(media.shape[1]):
            if matrizq:
                valor = dftipo[str(i + 1)]
            else:
                produto = dfmedia.index[i]
                valor = dftipo[produto]
            tipo_std[i, j] = int(dict_tipos[valor])

    variancia = np.zeros(media.shape)
    for i in range(media.shape[0]):
        for j in range(media.shape[1]):
            tipo = tipo_std[i, j]
            if tipo == 1:
                variancia[i, j] = desvio[i, j] ** 2
            elif tipo == 2:
                variancia[i, j] = (math.exp(desvio[i, j] ** 2) - 1) * (math.exp(2 * media[i, j] + desvio[i, j] ** 2))

    return variancia, tipo_std
