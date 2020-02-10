import numpy as np
import matplotlib.pyplot as plt

def dSIRdt(tSI, beta, epsg, eps, phi, rec, turn_over, migration):
    Ng = 1e10
    N = 1e8

    infectiong = beta*(1+epsg*np.cos(2*np.pi*(tSI[0])))*tSI[1]*tSI[2]
    dSg = - infectiong/Ng + (1-tSI[1])*turn_over
    dIg = infectiong - (turn_over+rec)*tSI[2] + migration*(tSI[4]-tSI[2])

    infection = beta*(1+eps*np.cos(2*np.pi*(tSI[0]+phi)))*tSI[3]*tSI[4]
    dS = - infection/N + (1-tSI[3])*turn_over
    dI = infection - (turn_over+rec)*tSI[4]  + migration*(tSI[2]-tSI[4])
    return np.array([1, dSg, dIg, dS, dI])


if __name__ == '__main__':
    fs=16
    eps = 0.50
    epsg = 0.1
    dt = 0.001

    rec =  36  # 10 days
    turn_over = 0.1 # 0.1/year
    migration = 1e-2
    t0 = 2019.8
    R0_vals = np.array([2, 2.5, 3, 4])
    # influx = 0.00001*50 # one in 10k people return sick from abroad per week


    for phi in [11/12, 1/12, 3/12]:
        plt.figure()
        plt.title(f"peak month: {phi*12}")
        for bi, beta in enumerate(R0_vals):
            SI_vs_t = [np.array([0, 1, 1, 1, 0.00])]
            while SI_vs_t[-1][0]<2:
                dSIR = dSIRdt(SI_vs_t[-1], beta*rec, epsg, eps, phi, rec, turn_over, migration)
                SI_vs_t.append(SI_vs_t[-1] + dSIR*dt)


            SI_vs_t = np.array(SI_vs_t)
            plt.plot(SI_vs_t[:,0]+t0, SI_vs_t[:,4], lw=3, c=f"C{bi}", ls='-', label=f'R0 = {beta}, seasonality={eps}')
            plt.plot(SI_vs_t[:,0]+t0, SI_vs_t[:,2], alpha=0.5, lw=2, c=f"C{bi}", ls='--')

        plt.show()
        plt.xlim([2019.8,2022])
        plt.xticks([2020.0, 2020.5, 2021, 2021.5])
        plt.ylim([0.1,1e10])

        plt.yscale('log')
        plt.xlabel('year', fontsize=fs)
        plt.ylabel('prevalence', fontsize=fs)
        plt.legend(loc=4, fontsize=fs*0.8)

        plt.savefig(f'figures/prevalance_{int(phi*12)}_eps{eps}_epsg{epsg}.pdf')


    plt.figure()
    phi=0
    for bi, beta in enumerate(R0_vals):
        SI_vs_t = [np.array([0, 1/beta, 1, 1/beta, 0.00])]
        while SI_vs_t[-1][0]<30:
            dSIR = dSIRdt(SI_vs_t[-1], beta*rec, epsg, eps, phi, rec, turn_over, migration)
            SI_vs_t.append(SI_vs_t[-1] + dSIR*dt)


        SI_vs_t = np.array(SI_vs_t)
        plt.plot(SI_vs_t[:,0]-10, SI_vs_t[:,4], lw=3, c=f"C{bi}", ls='-', label=f'R0 = {beta}, seasonality={eps}')
        plt.plot(SI_vs_t[:,0]-10, SI_vs_t[:,2], alpha=0.5, lw=2, c=f"C{bi}", ls='--')

        plt.show()
        plt.ylim([0.1,1e10])
        plt.xlim([0,20])

        plt.yscale('log')
        plt.xlabel('year', fontsize=fs)
        plt.ylabel('prevalence', fontsize=fs)
        plt.legend(fontsize=fs*0.8)

    plt.savefig(f'figures/prevalance_endemic_eps{eps}_epsg{epsg}.pdf')
