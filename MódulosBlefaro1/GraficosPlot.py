from matplotlib import pyplot as plt


def GraficoEAR(vetorear, taxadeframes, quadros):
    tam1 = len(vetorear)
    tam2 = len(taxadeframes)
    dif = tam2 - tam1
    if (dif != 0):
        taxadeframes = taxadeframes[:-dif]
    plt.plot(taxadeframes, vetorear, c='r', lw='1', marker='o', ms='1')
    plt.suptitle('EAR x Tempo')
    plt.ylabel('EAR')
    plt.xlabel('Segundos')
    plt.axis([0, (quadros) / 30, 0, 0.45])
    plt.grid(True)
    plt.show()
