import pandas as pd
import numpy as np
from scipy.stats import poisson
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

def dSIRdt_vec(S, I, t, params, turnover=0):
    '''
    vectorized derivative of SIR models in multiple populations.

    S, I are vectors with one entry for each population
    t is time
    params is an array of [[N, beta, rec, eps, theta, climate, containment, relative_migration],
                           [N, beta, rec, eps, theta, climate, containment, relative_migration], ...]

    '''
    infection = params[:,1]*(1 - params[:,6]*I**3/(0.03**3+I**3))*S*I*(1+params[:,3]*np.cos(2*np.pi*(t - params[:,4])))
    dS = -infection - turnover*(S-1)
    dI = infection - (params[:,2]+turnover)*I

    return dS, dI


def plot_many_population_scenario(R0=2, t0=2019.9, eps_temperate=0.5, eps_tropical=0.2):
    #R0 = 2     # together with eps0=0.5, this corresponds to 2.5 in winter
    rec = 36   # 10 day serial interval
    N0 = 1e7   # size of Wuhan
    eps0 = 0.5 # seasonality
    theta0 = 0.0 # peak transmissibility in Dec/Jan
    popsize_sigma = 1 # standard deviation of population size lognormal
    world_population = 7.6e9
    migration = 3e-3 # rate of moving per year anywhere
    migration_sigma = 2 # standard deviation migration rate lognormal
    containment_hubei = 0.5 # containment value for hubei. Strong containment measures in Hubei
    containment_world_range = 0.5 # assumes uniform distribution between no containment and 0.5 in other regions
    theta_temperate_sigma = 0.1  # standard deviation of the distribution of peak x-missibility in temperate regions
    regions = {"Northern":1, "Tropical":0,  "Southern":-1}
    population_turnover = 0.0 # rate at which people become susceptible again.
    under_reporting = 10

    #total number of populations
    n_pops = 1000
    case_counts = pd.read_csv('data/case_counts.tsv', sep='\t')
    # add Hubei population with parameters specified above
    #          population size, beta, rec, eps, theta, NH, containment, relative migration
    params = [[N0, R0*rec, rec, eps0, theta0, 1, containment_hubei, 1.0]]
    # initially fully susceptible with one case
    populations = [[1, 1/N0]]

    # construct other populations
    for i in range(n_pops-1):
        tmp = np.random.random() # draw NH, SH, tropical
        if tmp<0.4: # according to http://worldpopulationreview.com/countries/tropical-countries/
            climate = regions["Tropical"]
            eps = np.random.random()*eps_tropical
            theta = np.random.random()
        elif tmp<0.9: # 90% live in the northern hemisphere
            climate = regions["Northern"]
            eps = np.random.random()*eps_temperate
            theta = np.random.normal(0,theta_temperate_sigma)  # peak in Dec/Jan
        else:
            climate = regions["Southern"]
            eps = np.random.random()*eps_temperate
            theta = np.random.normal(0.5,theta_temperate_sigma) # peak in June/July

        # Limit R0 to have to be >= 0
        beta = max(0, np.random.normal(loc=R0, scale=1))*rec
        relative_migration = np.random.lognormal(-migration_sigma**2/2, migration_sigma)
        N = np.random.lognormal(np.log(world_population/n_pops)-popsize_sigma**2/2,popsize_sigma)
        containment = np.random.random()*containment_world_range
        # add initially uninfected population and parameters
        populations.append([1, 0])
        params.append([N, beta, rec, eps, theta, climate, containment, relative_migration])

    params = np.array(params)
    populations = [np.array(populations)]

    # start simulation
    t = [t0]
    dt = 0.001
    tmax = 2022
    while t[-1]<tmax:
        dS, dI = dSIRdt_vec(populations[-1][:,0], populations[-1][:,1], t[-1], params, turnover=population_turnover)
        populations.append(populations[-1] + dt*np.array([dS,dI]).T)

        I_tot = (params[:,0]*populations[-1][:,1]).sum()
        populations[-1][:,1] += poisson.rvs(migration*I_tot/n_pops*dt*params[:,7])/params[:,0]
        t.append(t[-1]+dt)

    populations = np.array(populations)
    # weigh each infection trajectory by its population size
    total_inf = (params[:,0]*populations[:,:,1]).sum(axis=1)
    params_by_region = {r:params[params[:,5]==regions[r],:] for r in regions}
    pops_by_region = {r:populations[:,params[:,5]==regions[r],:] for r in regions}


    #####################################################################
    ### plot figures
    #####################################################################
    colors = {"Northern":"C1", "Southern":"C2", "Tropical":"C3", "Hubei":"C4", "Total simulation":"C0", "Total observed":"C5"}

    label_set = set()
    def get_label(pi):
        if pi==0:
            label = 'Hubei'
        elif params[pi][5]==0:
            label = 'Tropical'
        elif params[pi][5]==1:
            label = 'North'
        elif params[pi][5]==-1:
            label = 'South'
        if label in label_set:
            return ''
        else:
            label_set.add(label)
            return label

    fs=16
    fig, axs = plt.subplots(1, 3, figsize=(14,5), sharey=True)
    for ax in axs:
        ax.plot(t, total_inf, lw=3, label='Total', c=colors["Total simulation"])
        ax.plot(case_counts["date"], case_counts["total"]*under_reporting,
                lw=3, label=f'observed (x{under_reporting})', c=colors[f"Total observed"])

    #find max R0 to adjust colour shading when plotting lines
    maxR0 = max(params[:,1]/rec)

    for ax,r in zip(axs, regions.keys()):
        ax.plot(t, (params_by_region[r][:,0]*pops_by_region[r][:,:,1]).sum(axis=1), lw=3, label=r+" total", c=colors[r])
        label_set = set()
        if r=='Northern':
            ax.plot(t, populations[:,0,1]*params[0, 0], lw=3, c=colors["Hubei"], label="Hubei")

        for pi in range(min(20, len(params_by_region[r]))):
            ax.plot(t, pops_by_region[r][:,pi,1]*params_by_region[r][pi, 0], lw=1.5, c=colors[r],
                    label='' if r in label_set else r, alpha=params[pi,1]/rec/maxR0)
            label_set.add(r)


        # make custom legend to show R0 values
        custom_lines = [Line2D([0], [0], color=colors[r], lw=2, alpha=(1/maxR0)),
                        Line2D([0], [0], color=colors[r], lw=2, alpha=(R0/maxR0)),
                        Line2D([0], [0], color=colors[r], lw=2, alpha=1)]
        first_legend = ax.legend(custom_lines, ["1",R0,round(maxR0,1)], title="R0", fontsize=fs*0.8, loc=4)
        plt.setp(first_legend.get_title(),fontsize=fs)
        ax.add_artist(first_legend)

        ax.legend(fontsize=fs*0.8, loc=8, ncol=1)
        ax.set_yscale('log')
        if ax==axs[0]:
            ax.set_ylabel('Cases', fontsize=fs)
        ax.set_xticks(np.array([2020.05, 2020.05, 2021.05, 2021.05, 2022.05]),
                               ['2020-01', '2020-07', '2021-01', '2021-07', '2022-01'])
        ax.tick_params(axis='x', labelsize=0.8*fs, labelrotation=30)
        ax.tick_params(axis='y', labelsize=0.8*fs)
        ax.set_xticklabels(ax.get_xticks(), horizontalalignment='right')
        ax.set_ylim([1,total_inf[:].max()*2])

    plt.tight_layout()
    plt.savefig(f'figures/global_3_panel_{R0}.pdf')


if __name__ == '__main__':

    for t0, R0 in zip([2019.6, 2019.9, 2020], [1.5, 2.0, 3.0]):
        plot_many_population_scenario(R0=R0)
