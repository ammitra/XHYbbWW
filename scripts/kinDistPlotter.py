'''
utility for plotting kinematic distributions per year. 
First run python THdistributions.py -y <year> to make the proper distribution files, then run this with the same flag. 

NOTE: This only runs on python 3. 
'''

import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplhep as hep
from root_numpy import hist2array
from glob import glob

# var : (xtitle, ytitle)
varnames = {
    'pt0': (r'Leading AK8 jet $p_{T}$', r'Events/20 GeV'),
    'pt1': (r'Sublead AK8 jet 1 $p_{T}$', r'Events/20 GeV'),
    'pt2': (r'Sublead AK8 jet 2 $p_{T}$', r'Events/20 GeV'),
    'HT':  (r'Sum of lead + two sublead jet $p_{T}$', r'Events/20 GeV'),
    'mjjj': (r'Trijet invariant mass [GeV]', r'Events/100 GeV'),
    'eta0': (r'Leading AK8 jet $\eta$',r'Events/10'),
    'eta1': (r'Sublead AK8 jet 1 $\eta$',r'Events/10'),
    'eta2': (r'Sublead AK8 jet 2 $\eta$',r'Events/10'),
    'phi0': (r'Leading AK8 jet $\varphi$',r'Events/10'),
    'phi1': (r'Sublead AK8 jet 1 $\varphi$',r'Events/10'),
    'phi2': (r'Sublead AK8 jet 2 $\varphi$',r'Events/10'),
    'PNetH0': (r'Leading AK8 jet ParticleNet H score',r'Events/0.01'),
    'PNetH1': (r'Sublead AK8 jet 1 ParticleNet H score',r'Events/0.01'),
    'PNetH2': (r'Sublead AK8 jet 2 ParticleNet H score',r'Events/0.01'),
    'PNetW0': (r'Leading AK8 jet ParticleNet W score',r'Events/0.01'),
    'PNetW1': (r'Sublead AK8 jet ParticleNet W score',r'Events/0.01'),
    'PNetW2': (r'Sublead AK8 jet ParticleNet W score',r'Events/0.01')
}


def plot(var,year,xtitle,ytitle):
    '''
    var (str)    = variable to plot
    year (str)   = year to plot
    xtitle (str) = title for x axis
    ytitle (str) = title for y axis

    '''
    histosBkg = []
    edgesBkg = []
    labelsBkg = []
    colorsBkg = []

    histosData = []
    edgesData = []
    labelsData = []
    colorsData = []

    histosSig = []
    edgesSig = []
    labelsSig = []
    colorsSig = []

    sigColorCounter = 0

    for name in ['Data','QCD','ttbar','MX1800-MY125','MX1800-MY1000','MX3000-MY2000']:
        # Just do this for now, since we only have 2017 official MC
        if 'MX' in name:
            tempFile = ROOT.TFile.Open('kinDist_{}_17.root'.format(name))
        else:
            tempFile = ROOT.TFile.Open('kinDist_{}_{}.root'.format(name, year))
        h = tempFile.Get(var)
        hist, edges = hist2array(h, return_edges=True)
        sigColors = ['green','blue','black']
        if name == 'Data':
            histosData.append(hist)
            edgesData.append(edges[0])
            labelsData.append('Data')
            colorsData.append('k')
        elif 'MX' in name:
            histosSig.append(hist)
            edgesSig.append(edges[0])
            mx = name.split('-')[0].split('MX')[-1]
            my = name.split('-')[-1].split('MY')[-1]
            labelsSig.append('({},{}) GeV'.format(mx,my))
            colorsSig.append(sigColors[sigColorCounter])
            sigColorCounter += 1
        else:
            histosBkg.append(hist)
            edgesBkg.append(edges[0])
            if name == 'QCD':
                labelsBkg.append('Multijets')
                colorsBkg.append('y')
            elif name == 'VJets':
                labelsBkg.append('V+jets')
                colorsBkg.append('aquamarine')
            elif name == 'ttbar':
                labelsBkg.append(r'$t\bar{t}$')
                colorsBkg.append('r')

    # QCD scaling to data
    hData = histosData[0]
    hQCD = histosBkg[0]
    scale = np.sum(hData)/np.sum(hQCD)
    histosBkg[0] = histosBkg[0] * scale

    # convert data to scatter
    scatterData = (edgesData[0][:-1] + edgesData[0][1:])/2
    errorsData = np.sqrt(histosData[0])

    # calculate ratio and errors
    hTotalBkg = np.sum(histosBkg, axis=0)
    errorsTotalBkg = np.sqrt(hTotalBkg)

    for i, val in enumerate(hTotalBkg):
        if (val == 0): hTotalBkg[i] = 0.01
    
    hRatio = np.divide(histosData[0], hTotalBkg)
    errorsRatio = []
    for i in range(len(hRatio)):
        f2 = hRatio[i] * hRatio[i]
        a2 = errorsData[i] * errorsData[i] / (histosData[0][i] * histosData[0][i])
        b2 = errorsTotalBkg[i] * errorsTotalBkg[i] / (hTotalBkg[i] * hTotalBkg[i])
        sigma2 = f2 * (a2+b2)
        sigma = np.sqrt(sigma2)
        errorsRatio.append(sigma)
    errorsRatio = np.asarray(errorsRatio)

    plt.style.use([hep.style.CMS])
    f, axs = plt.subplots(2, 1, sharex=True, sharey=False, gridspec_kw={'height_ratios':[4,1],'hspace':0.05})
    axs = axs.flatten()
    plt.sca(axs[0])
    hep.histplot(histosBkg, edgesBkg[0], stack=False, ax=axs[0], label=labelsBkg, histtype='fill', facecolor=colorsBkg, edgecolor='black')
    plt.errorbar(scatterData, histosData[0], yerr=errorsData, fmt='o', color='k', label=labelsData[0])
    if ('PNet' in var) or ('mj' in var) or ('HT' in var):
        for i,h in enumerate(histosSig):
            hep.histplot(h,edgesSig[i],stack=False,ax=axs[0],label=labelsSig[i],linewidth=3,zorder=2,color=colorsSig[i])
    axs[0].set_yscale('log')
    axs[0].legend()
    axs[1].set_xlabel(xtitle)
    axs[0].set_ylabel(ytitle)
    plt.ylabel(ytitle, horizontalalignment='right', y=1.0)
    axs[1].set_ylabel("Data/MC")
    yMax = axs[0].get_ylim()
    axs[0].set_ylim([0.01, yMax[1]*10000])
    hep.cms.text("Preliminary", loc=1)
    if ('mj' in var) or ('PNet' in var):
        plt.legend(loc='lower left', bbox_to_anchor=(0.55,0.5), fontsize='small')
    else:
        plt.legend(loc='best')

    plt.sca(axs[1])
    axs[1].axhline(y=1.0, xmin=0, xmax=1, color='r')
    axs[1].set_ylim([0.,2.1])
    plt.xlabel(xtitle, horizontalalignment='right', x=1.0)
    plt.errorbar(scatterData, hRatio, yerr=errorsRatio, fmt='o', color='k')

    plt.savefig('{}_{}.png'.format(var,year))
    plt.savefig('{}_{}.pdf'.format(var,year))
    plt.clf()

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-y', type=str, dest='era',
                        action='store', required=True,
                        help='Year to process')
    args = parser.parse_args()

    for var, titles in varnames.items():
        plot(var, args.era, titles[0], titles[1])
