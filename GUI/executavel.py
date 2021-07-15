import os
import sys
# sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import matplotlib
import pandas as pd
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog

from utils import pandasModel, coluna_fantasma, criterio_de_corte, alocar, calcular_inventario

# Ensure using PyQt5 backend
matplotlib.use('QT5Agg')

# Pegar estrutura (tem que etar na mesma pasta)
path = os.path.dirname(__file__)  # uic paths from itself, not the active dir, so path needed
qtCreatorFile = "estrutura_acv.ui"  # Ui file name, from QtDesigner, assumes in same folder as this .py

Ui_MainWindow, QtBaseClass = uic.loadUiType(path + '\\' + qtCreatorFile)  # process through pyuic


class MyApp(QMainWindow, Ui_MainWindow):  # gui class
	def __init__(self, parent=None):
		# The following sets up the gui via Qt
		super(MyApp, self).__init__(parent)
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)

		self.ui.tabWidget.setCurrentIndex(0)

		self.ui.btn_carregar.clicked.connect(self.fun_carregar_arquivo)
		self.ui.btn_procurar.clicked.connect(self.fun_procurar_arquivo)
		self.ui.btn_calc_inv.clicked.connect(self.fun_calc_inv1)
		self.ui.btn_calcular_matrizes.clicked.connect(self.calcular_matrizes)
		self.ui.cb_prod1_aloc.currentTextChanged.connect(self.update_produto2)
		self.ui.btn_calc_inventario.clicked.connect(self.calcular_inventario)

	# self.ui.stackedWidget.setCurrentIndex(0)

	def fun_procurar_arquivo(self):
		options = QFileDialog.Options()
		fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "All Files (*)",
		                                          options=options)
		if fileName:
			self.ui.file_field.setText(fileName)

	def fun_carregar_arquivo(self):
		filename = self.ui.file_field.text()
		inputed = pd.read_excel(filename)
		inputed.fillna(0, inplace=True)
		ncols = len(inputed.columns)
		self.nprocessos = ncols - 3
		processos = [f'P{i}' for i in range(1, self.nprocessos + 1)]

		self.dfA = inputed[inputed['Intermediário'] == 1][['Produto'] + processos].copy()
		modelA = pandasModel(self.dfA.copy())
		self.dfA.set_index('Produto', inplace=True)

		self.dfB = inputed[inputed['Intermediário'] == 0][['Produto'] + processos].copy()
		modelB = pandasModel(self.dfB.copy())
		self.dfB.set_index('Produto', inplace=True)

		self.dfk = inputed[inputed['Intermediário'] == 1][['Produto', 'Fluxo de referência']].copy()
		modelk = pandasModel(self.dfk.copy())
		self.dfk.set_index('Produto', inplace=True)

		nprodutos = len(self.dfA)

		self.mostrar_table_view(self.ui.tvA, modelA, self.ui.tvB, modelB, self.ui.tvk, modelk)

		self.ui.lineEditnprocess.setText(str(self.nprocessos))
		self.ui.lineEditnprod.setText(str(nprodutos))
		self.ui.btn_calc_inv.setEnabled(True)

		self.ui.cb_prod_criterio.clear()
		self.ui.cb_prod_criterio.addItems(self.dfA.index.to_list())
		self.ui.cb_proc_aloc.clear()

		self.ui.cb_proc_aloc.addItems([f'{i}' for i in range(1, self.nprocessos + 1)])
		self.ui.cb_prod1_aloc.clear()
		self.ui.cb_prod1_aloc.addItems(self.dfA.index.to_list())
		self.update_produto2()

	def mostrar_table_view(self, ta, ma, tb, mb, tk, mk):
		for tvm in [(ta, ma, False), (tb, mb, False), (tk, mk, True)]:
			tvm[0].setModel(tvm[1])
			for column in range(tvm[1].columnCount()):
				if column == 0:
					tvm[0].setColumnWidth(column, 70)
				else:
					if tvm[2] == True:
						tvm[0].setColumnWidth(column, 120)
					else:
						tvm[0].setColumnWidth(column, 60)



	def fun_calc_inv1(self):
		self.ui.tabWidget.setCurrentIndex(1)
		self.ui.group_metodo.setEnabled(True)
		self.ui.btn_calcular_matrizes.setEnabled(True)

	def update_produto2(self):
		produtos_sem_o_1 = list(self.dfA.index.to_list())
		produtos_sem_o_1.remove(str(self.ui.cb_prod1_aloc.currentText()))
		self.ui.cb_prod2_aloc.clear()
		self.ui.cb_prod2_aloc.addItems(produtos_sem_o_1)

	def calcular_matrizes(self):
		botoes = [self.ui.fantasma, self.ui.corte, self.ui.alocacao]
		for ind, val in enumerate(botoes):
			if val.isChecked(): metodo = ind

		if metodo == 0:
			self.A, self.B, self.k = coluna_fantasma(self.dfA, self.dfB, self.dfk, self.nprocessos)
		elif metodo==1:
			produto = str(self.ui.cb_prod_criterio.currentText())
			self.A, self.B, self.k = criterio_de_corte(self.dfA, self.dfB, self.dfk, produto)

		elif metodo==2:
			processo = str(self.ui.cb_proc_aloc.currentText())
			produto1 = str(self.ui.cb_prod1_aloc.currentText())
			produto2 = str(self.ui.cb_prod2_aloc.currentText())
			self.A, self.B, self.k = alocar(self.dfA, self.dfB, self.dfk, self.nprocessos, processo, produto1, produto2)

		modelA2 = pandasModel(round(self.A.reset_index().copy(),3))
		modelB2 = pandasModel(round(self.B.reset_index().copy(),3))
		modelk2 = pandasModel(round(self.k.reset_index().copy(),3))

		self.mostrar_table_view(self.ui.tvA2, modelA2, self.ui.tvB2, modelB2, self.ui.tvk2, modelk2)
		self.ui.btn_calc_inventario.setEnabled(True)

	def calcular_inventario(self):
		self.inva, self.binva, self.M = calcular_inventario(self.A, self.B, self.k)
		modelinva = pandasModel(round(self.inva.copy(), 3))
		modelbinva = pandasModel(round(self.binva.copy(), 3))
		modelm = pandasModel(round(self.M.reset_index().rename(columns={'index':'Produto'}).copy(), 3))
		self.mostrar_table_view(self.ui.tvinva, modelinva, self.ui.tvbinva, modelbinva, self.ui.tvm, modelm)
		self.ui.tabWidget.setCurrentIndex(2)









if __name__ == "__main__":
	app = QApplication(sys.argv)  # instantiate a QtGui (holder for the app)
	window = MyApp()
	window.show()
	sys.exit(app.exec_())

# EOF
