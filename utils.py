import numpy as np
import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, Qt

def calcular_inventario(A,B,k):
    inva = np.linalg.inv(A.to_numpy())
    binva = np.matmul(B.to_numpy(), inva)
    M = np.matmul(binva, k.to_numpy())

    dfinva = pd.DataFrame(data=inva[0:, 0:],
                          index=[i for i in range(inva.shape[0])],
                          columns=['Column' + str(i) for i in range(inva.shape[1])])

    dfbinva = pd.DataFrame(data=binva[0:, 0:],
                           index=[i for i in range(binva.shape[0])],
                           columns=['Column' + str(i) for i in range(binva.shape[1])])

    dfM = pd.DataFrame(data=M[0:, 0:],
                       index=[i for i in range(M.shape[0])],
                       columns=['Emissão' for i in range(M.shape[1])])

    dict_map_index = {ind: val for ind, val in enumerate(B.index.to_list())}
    dfM.rename(dict_map_index, inplace=True)

    return dfinva, dfbinva, dfM

def coluna_fantasma(A, B, k, nprocessos):
    dfa = A.copy()
    dfb = B.copy()
    dfk = k.copy()
    
    fantasma = f'P{nprocessos+1}'
    dfa[fantasma] = 0
    dfa.loc[dfa.index[-1], fantasma]= 1
    dfb[fantasma]=0
    
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

    dfa[processo_a_ser_criado] = dfa[processo_a_ser_dividido]*prop_el2 # vai ser do fofo
    dfa.at[produto1, processo_a_ser_criado] = 0
    dfa.at[produto2, processo_a_ser_criado] = qtd_el2

    dfa[processo_a_ser_dividido] = dfa[processo_a_ser_dividido]*prop_el1 # vai ser do aço
    dfa.at[produto1, processo_a_ser_dividido] = qtd_el1
    dfa.at[produto2, processo_a_ser_dividido] = 0

    dfb[processo_a_ser_criado] = dfb[processo_a_ser_dividido]*prop_el2 # vai ser do aço
    dfb[processo_a_ser_dividido] = dfb[processo_a_ser_dividido]*prop_el1 # vai ser do aço
    
    return dfa, dfb, dfk



class pandasModel(QAbstractTableModel):

    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None