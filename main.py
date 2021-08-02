import numpy as np
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as colors

matplotlib.rcParams['figure.figsize'] = (8, 6)
matplotlib.rcParams.update({'font.size': 14})
plt.rc('text', usetex=False)
plt.rc('font', family='serif')

from utils import ler_entradas, calcular_variancias, calcular_inventario

# os.system('clear')  # Limpar o console
# Constantes de print
separador = 45 * '#'
W = '\033[0m'  # Cor branca
Bcor = '\033[34m'  # Cor azul
G = '\033[32m'  # Cor verde
R = '\033[31m'  # Cor vermelha

## LER ENTRADAS
filename = 'entradas.xlsx'
dfa, dfb, dfk, dfq, dfstda, dfstdb, dfstdq, dtipos_stdp, dtipos_stdq = ler_entradas(filename)

## TRANSFORMAR DE DATAFRAME PRA NUMPY
A, B, matriz_q = dfa.to_numpy(), dfb.to_numpy(), dfq.to_numpy()
std_a, std_b, std_q = dfstda.to_numpy(), dfstdb.to_numpy(), dfstdq.to_numpy()

## CALCULAR VARIÂNCIAS
var_a, tipos_a = calcular_variancias(A, std_a, dtipos_stdp, dfa)
coef_a = abs(np.true_divide(var_a, A)*100)
var_b, tipos_b = calcular_variancias(B, std_b, dtipos_stdp, dfb)
coef_b = abs(np.true_divide(var_b, B)*100)
var_q, tipos_q = calcular_variancias(matriz_q, std_q, dtipos_stdq, dfq, True)

# CALCULAR INVENTÁRIO
dfs, dfg, dflambda, inva = calcular_inventario(dfa, dfb, dfk)

## TRANSFORMAR DE DATAFRAME PRA NUMPY
matriz_s, matriz_g, matriz_lambda = dfs.to_numpy(), dfg.to_numpy(), dflambda.to_numpy()

# CALCULAR h
matriz_h = np.matmul(matriz_q, matriz_g)
dfh = pd.DataFrame(matriz_h)
dfh.index = dfq.index
dfh.rename(columns={0: 'Caracterização'}, inplace=True)

# PRINTAR INVENTÁRIO
print(f'{separador}\nA{G}\n{dfa.reset_index()}{W}')
print(f'{separador}\nVariância de A{G}\n{var_a}{W}')
print(f'{separador}\nCoeficiente de variação de A (%){G}\n{coef_a}{W}')
print(f'{separador}\nB{G}\n{dfb.reset_index()}{W}')
print(f'{separador}\nVariância de B{G}\n{var_b}{W}')
print(f'{separador}\nCoeficiente de variação de B (%){G}\n{coef_b}{W}')
print(f'{separador}\nk{G}\n{dfk.reset_index()}{W}')
print(f'{separador}\ns{G}\n{dfs.reset_index()}{W}')
print(f'{separador}\ng{G}\n{dfg.reset_index()}{W}')
print(f'{separador}\nlambda{G}\n{dflambda}{W}')
print(f'{separador}\nA-1{G}\n{inva}{W}')
print(f'{separador}\nQ{G}\n{dfq}{W}')
print(f'{separador}\nVariância de q{G}\n{var_q}{W}')
print(f'{separador}\nh{G}\n{dfh}{W}')

######################## ANÁLISE DE PERTURBAÇÃO #########################
#########################################################################
#################### cálculos TABELA 3 - Heijungs(2010) #################
#########################################################################

print(f'\n{separador}\nANÁLISE DE PERTURBAÇÃO\n{separador}\n')

print(f'{separador}\nPerturbação de s em A:')
# calcular ∂sk/∂aij = −(A−1)ki * sj (IMPRIME ELEMENTOS SEPARADOS)
dsda = []
for k in range(len(matriz_s)):
	dsda_k = np.zeros(A.shape)
	for i in range(A.shape[0]):
		for j in range(A.shape[1]):
			dsda_k[i, j] = -inva[k, i] * matriz_s[j]
	dsda.append(dsda_k)
	print(f'\n{W}∂s{k + 1}/∂aij = −(A−1)ki * sj\n{G}{dsda[k]}{W}')

print(f'\n{separador}\nPerturbação de g em A:')
# calcular ∂gk/∂aij = -λki * sj (IMPRIME ELEMENTOS DENTRO DE UMA LISTA)
dgda = []
for k in range(len(matriz_g)):
	dgda_k = np.zeros(A.shape)
	for i in range(A.shape[0]):
		for j in range(A.shape[1]):
			dgda_k[i, j] = -matriz_lambda[k, i] * matriz_s[j]
	dgda.append(dgda_k)
	print(f'\n{W}∂g{k + 1}/∂aij = -λki * sj\n{G}{dgda[k]}{W}')

print(f'\n{separador}\nPerturbação de h em A:')
# calcular ∂hk/∂aij = -sj * ∑l (qkl * λli)
dhda = []
for k in range(len(matriz_h)):
	dhda_k = np.zeros(A.shape)
	for i in range(A.shape[0]):
		for j in range(A.shape[1]):
			soma = 0
			for l in range(matriz_q.shape[1]):
				soma += matriz_q[k, l] * matriz_lambda[l, i]
			dhda_k = -matriz_s[j] * soma
	dhda.append(dhda_k)
	print(f'\n{W}∂h{k + 1}/∂aij = -sj * ∑l (qkl * λli)\n{G}{dhda[k]}{W}')

print(f'\n{separador}\nPerturbação de g em B:')
# calcular ∂gk/∂bij = sj * δik
dgdb = []
for k in range(len(matriz_g)):
	dgdb_k = np.zeros(B.shape)
	for i in range(B.shape[0]):
		for j in range(B.shape[1]):
			if i == k:
				dgdb_k[i, j] = matriz_s[j]
			else:
				dgdb_k[i, j] = 0
	dgdb.append(dgdb_k)
	print(f'\n{W}∂g{k + 1}/∂bij = sj * δik\n{G}{dgdb[k]}{W}')

print(f'\n{separador}\nPerturbação de h em B:')
# calcular ∂hk/∂bij = qki * sj
dhdb = []
for k in range(len(matriz_h)):
	dhdb_k = np.zeros(B.shape)
	for i in range(B.shape[0]):
		for j in range(B.shape[1]):
			dhdb_k[i, j] = matriz_q[k, i] * matriz_s[j]
	dhdb.append(dhdb_k)
	print(f'\n{W}∂h{k + 1}/∂bij = qki * sj\n{G}{dhdb[k]}{W}')

print(f'\n{separador}\nPerturbação de h em Q:')
# calcular ∂hk/∂qij = gj * δik
dhdq = []
for k in range(len(matriz_h)):
	dhdq_k = np.zeros(matriz_q.shape)
	for i in range(matriz_q.shape[0]):
		for j in range(matriz_q.shape[1]):
			if i == k:
				dhdq_k[i, j] = matriz_g[j]
			else:
				dhdq_k[i, j] = 0
	dhdq.append(dhdq_k)
	print(f'\n{W}∂h{k + 1}/∂qij = gj * δik\n{G}{dhdq[k]}{W}')

######################## ANÁLISE DE SEN. RELAT. #########################
#########################################################################
#################### cálculos TABELA 4 - Heijungs(2010) #################
#########################################################################

print(f'\n{separador}\nCOEFICIENTES DE SENSITIVIDADE RELATIVOS\n{separador}\n')
print(f'Sigmas em a:')
# calcular (∂sk/sk) / (∂aij/aij) = − aij / sk * (A−1)ki * sj
sigmas = []
for k in range(len(matriz_s)):
	sigma_k = np.zeros(A.shape)
	for i in range(A.shape[0]):
		for j in range(A.shape[1]):
			sigma_k[i, j] = -A[i, j] / matriz_s[k] * inva[k, i] * matriz_s[j]
	sigmas.append(sigma_k)
	print(f'\nσ{k + 1}(a) = (∂s{k}/s{k}) / (∂aij/aij) = − aij / sk * (A−1)ki * sj\n{G}{sigmas[k]}{W}')

print(f'\n{separador}\n\nGamas em a:')
# calcular (∂gk/gk) / (∂aij/aij) = − aij / gk * λki * sj

gamas_a = []
for k in range(len(matriz_g)):
	gama_k = np.zeros(A.shape)
	for i in range(A.shape[0]):
		for j in range(A.shape[1]):
			gama_k[i, j] = -A[i, j] / matriz_g[k] * matriz_lambda[k, i] * matriz_s[j]
	gamas_a.append(gama_k)
	print(f'\nγ{k + 1}(a) = (∂g{k}/g{k}) / (∂aij/aij) = − aij / gk * λki * sj\n{G}{gamas_a[k]}{W}')

print(f'\n{separador}\n\nGamas em b:')
# calcular (∂gk/gk) / (∂aij/aij) = − aij / gk * λki * sj

gamas_b = []
for k in range(len(matriz_g)):
	gama_k = np.zeros(B.shape)
	for i in range(B.shape[0]):
		for j in range(B.shape[1]):
			if i == k:
				gama_k[i, j] = B[i, j] / matriz_g[k] * matriz_s[j]
			else:
				gama_k[i, j] = 0
	gamas_b.append(gama_k)
	print(f'\nγ{k + 1}(b) = (∂g{k}/g{k}) / (∂bij/bij) = bij / gk * sj * deltaik \n{G}{gamas_b[k]}{W}')

# calcular (∂gk/gk) / (∂bij/bij) =	bij / gk * sj * δik


# calcular (∂hk/hk) / (∂aij/aij) =	− aij / hk * sj * ∑l (qkl * λli)


# calcular (∂hk/hk) / (∂bij/bij) = bij / hk * qki * sj


# calcular (∂hk/hk) / (∂qij/qij) = qij / hk * gj * δik


######################## ANÁLISE DE INCERTEZAS  #########################
#########################################################################
#################### cálculos TABELA 5 - Heijungs(2010) #################
#########################################################################
print(f'\n{separador}\nINCERTEZAS\n{separador}\n')

# Calcular variância de s
var_s = np.zeros(matriz_s.shape)
for k in range(len(matriz_s)):
	# print(f'Para S{k}:')
	soma = 0
	for i in range(A.shape[0]):
		for j in range(A.shape[1]):
			valor = matriz_s[j] ** 2 * var_a[i, j] * inva[k, i] ** 2
			soma += valor
	var_s[k] = soma

print(f'Variância de s\n{G}{var_s}{W}')
coef_s = abs(np.true_divide(var_s, matriz_s)*100)
print(f'\nCoeficiente de variação de s (%)\n{G}{coef_s}{W}')

# Calcular variância de g
var_g1 = np.zeros(matriz_g.shape)
var_g2 = np.zeros(matriz_g.shape)
var_g = np.zeros(matriz_g.shape)

for k in range(len(matriz_g)):
	soma1 = 0
	for i in range(A.shape[0]):
		soma2 = 0
		for j in range(A.shape[1]):
			soma1 += (matriz_s[j] * matriz_lambda[k, i]) ** 2 * var_a[i, j]
			soma2 += matriz_s[j] ** 2 * var_b[k, j]

	var_g1[k] = soma1
	var_g2[k] = soma2
	var_g[k] = soma1 + soma2

print(f'\n{W}\nVariância de g\n{G}{var_g}{W}')
coef_g = abs(np.true_divide(var_g, matriz_g)*100)
print(f'\nCoeficiente de variação de g (%)\n{G}{coef_g}{W}')

# Calcular variância de h
var_h1 = np.zeros(matriz_h.shape)
var_h2 = np.zeros(matriz_h.shape)
var_h3 = np.zeros(matriz_h.shape)
var_h = np.zeros(matriz_h.shape)

for k in range(len(matriz_h)):
	soma1 = 0
	soma2 = 0
	for i in range(matriz_h.shape[0]):
		soma3 = 0
		for j in range(matriz_h.shape[1]):
			soma11 = 0
			for l in range(matriz_q.shape[0]):
				soma11 += matriz_q[k, l] * matriz_lambda[l, i]
			soma1 += (matriz_s[j] * soma11) ** 2 * var_a[i, j]
			soma2 += (matriz_s[j] + matriz_q[k, i]) ** 2 * var_b[i, j]
			soma3 += matriz_g[j] ** 2 * var_q[i, j]

	var_h1[k] = soma1
	var_h2[k] = soma2
	var_h3[k] = soma3
	var_h[k] = soma1 + soma2 + soma3

print(f'\n{W}\nVariância de h\n{G}{var_h}{W}')
coef_h = abs(np.true_divide(var_h, matriz_h)*100)
print(f'\nCoeficiente de variação de h (%)\n{G}{coef_h}{W}')

######################## ANÁLISE DE CONTRIBUI.  #########################
#########################################################################
#################### cálculos TABELA 6 - Heijungs(2010) #################
#########################################################################
print(f'\n{separador}\nCONTRIBUIÇÕES\n{separador}\n')

# Calcular Zeta de s em a
print('Zeta de s em a:\n')
zeta_sa = []
for k in range(len(matriz_s)):
	zeta_k = np.zeros(A.shape)
	for i in range(A.shape[0]):
		for j in range(A.shape[1]):
			zeta_k[i,j] = (inva[k,i]*matriz_s[j])**2 * var_a[i,j] / var_s[k]
	zeta_sa.append(zeta_k)
	print(f'Zeta(s{k+1}, aij)\n{G}{zeta_sa[k]}{W}')

# Calcular Zeta de g em a
print(f'\n{separador}\nZeta de g em a:\n')
zeta_ga = []
for k in range(len(matriz_g)):
	zeta_k = np.zeros(A.shape)
	for i in range(A.shape[0]):
		for j in range(A.shape[1]):
			zeta_k[i,j] = (matriz_s[j]*matriz_lambda[k,i])**2 * var_a[i,j] / var_g[k]
	zeta_ga.append(zeta_k)
	print(f'Zeta(g{k+1}, aij)\n{G}{zeta_ga[k]}{W}')

# Calcular Zeta de g em b
print(f'\n{separador}\nZeta de g em b:\n')
zeta_gb = []
for k in range(len(matriz_g)):
	zeta_k = np.zeros(B.shape)
	for i in range(B.shape[0]):
		for j in range(B.shape[1]):
			if i==k:
				zeta_k[i,j] = (matriz_s[j])**2 * var_b[i,j] / var_g[k]
			else:
				zeta_k[i, j] = 0
	zeta_gb.append(zeta_k)
	print(f'Zeta(g{k+1}, bij)\n{G}{zeta_gb[k]}{W}')

# Calcular Zeta de h em a
print(f'\n{separador}\nZeta de h em a:\n')
zeta_ha = []
for k in range(len(matriz_h)):
	zeta_k = np.zeros(A.shape)
	for i in range(A.shape[0]):
		for j in range(A.shape[1]):
			soma = 0
			for l in range(matriz_q.shape[1]):
				soma += matriz_q[k,l] * matriz_lambda [l,i]
			zeta_k[i,j] = (matriz_s[j] * soma)**2 * var_a[i,j] / var_h[k]
	zeta_ha.append(zeta_k)
	print(f'Zeta(h{k+1}, aij)\n{G}{zeta_ha[k]}{W}')

# Calcular Zeta de h em b
print(f'\n{separador}\nZeta de h em b:\n')
zeta_hb = []
for k in range(len(matriz_h)):
	zeta_k = np.zeros(B.shape)
	for i in range(B.shape[0]):
		for j in range(B.shape[1]):
			zeta_k[i,j] = (matriz_s[j] * matriz_q[k,i])**2 * var_b[i,j] / var_h[k]
	zeta_hb.append(zeta_k)
	print(f'Zeta(h{k+1}, bij)\n{G}{zeta_hb[k]}{W}')

# Calcular Zeta de h em a
print(f'\n{separador}\nZeta de h em q:\n')
zeta_hq = []
for k in range(len(matriz_h)):
	zeta_k = np.zeros(matriz_q.shape)
	for i in range(matriz_q.shape[0]):
		for j in range(matriz_q.shape[1]):
			zeta_k[i,j] = matriz_g[j] ** 2 * var_q[k,j] / var_h[k]
	zeta_hq.append(zeta_k)
	print(f'Zeta(h{k+1}, qij)\n{G}{zeta_hq[k]}{W}')

y_a = coef_a.flatten(order='C')

x_to_plot = []


color_plotar = ['blue', 'green', 'orange', 'black']
fig, ax = plt.subplots()

for k in range(len(matriz_s)):
	x_to_plot = zeta_sa[k].flatten(order='C')
	ax.plot(x_to_plot,y_a, 'o', label = f's = {k+1}', color = color_plotar[k], linewidth='2')
for k in range(len(matriz_g)):
	x_to_plot = zeta_ga[k].flatten(order='C')
	ax.plot(x_to_plot,y_a, 'x', label = f'g = {k+1}', color = color_plotar[k], linewidth='2')
ax.set(xlabel = f'$\zeta$(s, aij)', ylabel = 'Coeficiente de variação de A (%)')
ax.legend()
plt.grid()
fig.savefig(f'Figuras\\\\tau.png', dpi=600)