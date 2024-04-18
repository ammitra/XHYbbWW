'''
utility for plotting the signal templates under the influence of variations in tagging     systematics.
'''
import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplhep as hep
from root_numpy import hist2array
from glob import glob

def plot(sigmass, year, systematics):
    histos_x = []
    histos_y = []
    edges_x  = []
    edges_y  = []
    labels   = ['Nominal','Wqq up','Wqq down','Hbb up','Hbb down']
    colors   = ['black','blue','blue','red','red']              # hard code
    styles   = ['solid','dashed','dotted','dashed','dotted']    # hard code
    maxX = 0
    maxY = 0
    for projection in ['X','Y']:
        print('plotting %s projection %s'%(sigmass, projection))
        for syst in systematics:
            f = ROOT.TFile.Open(baseFile.format(sigmass=sigmass,year=year,syst=syst))
            h = f.Get(baseHist)
            nbins = getattr(h,'GetNbins%s'%projection)()
            h_proj = getattr(h,'Projection%s'%projection)('',1,nbins)
            maxProj = h_proj.GetMaximum()
            hist, edge = hist2array(h_proj, return_edges=True)
            if projection == 'X':
                histos_x.append(hist)
                edges_x.append(edge[0])
                maxX = maxProj
            else:
                histos_y.append(hist)
                edges_y.append(edge[0])
                maxY = maxProj
            f.Close()

    plt.style.use([hep.style.CMS])
    f, axs = plt.subplots(1, 2, sharey=False, figsize=(15, 8))
    axs = axs.flatten()
    # X projection
    axs[0].set_title(r'$m_{X}$ projection')
    hep.histplot(histos_x, edges_x[0], stack=False, ax=axs[0], label=labels, histtype='step', linestyle=styles, color=colors)
    handlesX, labelsX = axs[0].get_legend_handles_labels()
    axs[0].legend(handlesX,labelsX)
    axs[0].set_xlabel(r'$m_{X}$ [GeV]')
    axs[0].set_ylabel('Events')
    #axs[1].set_ylim([0., maxX*1.3])
    #hep.cms.text("Preliminary", loc=1, ax=axs[0])

    # Y projection 
    axs[1].set_title(r'$m_{Y}$ projection')
    hep.histplot(histos_y, edges_y[1], stack=False, ax=axs[1], label=labels, histtype='step', linestyle=styles, color=colors)
    handlesY, labelsY = axs[1].get_legend_handles_labels()
    axs[1].legend(handlesY,labelsY)
    axs[1].set_xlabel(r'$m_{Y}$ [GeV]')
    axs[1].set_ylabel('Events')
    #axs[1].set_ylim([0., maxY*1.3])
    #hep.cms.text("Preliminary", loc=1, ax=axs[1])
    plt.legend(loc='best')

    plt.savefig('plots/SignalSystematics_{}_{}.png'.format(sigmass,year))
    plt.savefig('plots/SignalSystematics_{}_{}.pdf'.format(sigmass,year))


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='setname',
                        action='store', required=True,
                        help='Setname to process.')
    parser.add_argument('-y', type=str, dest='year',
                        action='store', required=True,
                        help='Year of set (16APV, 16, 17, 18).')

    args = parser.parse_args()

    baseFile = 'rootfiles/XHYbbWWselection_HT0_NMSSM-XHY-{sigmass}_{year}{syst}.root'
    baseHist = 'MXvMY_SR_pass_msoftdrop__nominal'
    systs = ['','_PNetWqq_up','_PNetWqq_down','_PNetHbb_up','_PNetHbb_down']

    plot(args.setname, args.year, systs)
