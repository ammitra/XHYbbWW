'''
utility for plotting the MC templates under the influence of variations in all of the systematics. 
- JECs are stored in separate files
- other systs (including tagging) are stored in the nominal file
'''
import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplhep as hep
from root_numpy import hist2array
from glob import glob

def plot(setname, year, region):
    # Get the base file for the process and base histogram
    nomFileName = baseFile.format(setname=setname,year=year,syst='')
    nomHistName = f'MXvMY_{region}__nominal'
    nomFile = ROOT.TFile.Open(nomFileName,'READ')
    nomHist = nomFile.Get(nomHistName)
    # Get a list of all unique systematics, ordered up/down
    systs = list(dict.fromkeys([k.GetName().split('__')[-1] for k in nomFile.GetListOfKeys() if ('nominal' not in k.GetName() and k.GetName() != 'cutflow')]))
    for projection in ['X','Y']:
        # store the histograms and information
        histos = []
        edges  = []
        labels = ['Nominal']
        colors = ['black','red','blue']
        styles = ['solid','solid','dashed']
        maxVal = 0
        # Get the projection of the nominal histogram
        nbins   = getattr(nomHist,'GetNbins%s'%projection)()
        hproj   = getattr(nomHist,'Projection%s'%projection)('',1,nbins)
        maxproj = hproj.GetMaximum()
        hist, edge = hist2array(hproj, return_edges=True)
        # Add it to the lists
        histos.append(hist)
        edges.append(edge[0])
        # get the systs and plot
        for i in range(0, len(systs)-1, 2):
            syst_up = systs[i]
            syst_dn = systs[i+1]
            ls = labels.copy()
            ls.append(syst_up)
            ls.append(syst_dn)
            print(f'Plotting {projection}-projection for systs {syst_up}, {syst_dn}')
            hist_up = nomFile.Get(nomHistName.replace('nominal',syst_up))
            hist_dn = nomFile.Get(nomHistName.replace('nominal',syst_dn))
            proj_up = getattr(hist_up,'Projection%s'%projection)('',1,nbins)
            proj_dn = getattr(hist_dn,'Projection%s'%projection)('',1,nbins)
            h_up, e_up = hist2array(proj_up, return_edges=True)
            h_dn, e_dn = hist2array(proj_dn, return_edges=True)
            hs = histos.copy()
            hs.append(h_up)
            hs.append(h_dn)
            es = edges.copy()
            es.append(e_up[0])
            es.append(e_dn[0])
            assert(hs[1][12] == hs[2][12])
            # Plot
            plt.style.use([hep.style.CMS])
            f, axs = plt.subplots(figsize=(12, 8), dpi=200)
            axs.set_title(r'%s %s, %s %s-projection'%(setname,year,region,projection))
            hep.histplot(hs, es[0], stack=False, ax=axs, label=ls, histtype='step', linestyle=styles, color=colors)
            handles, labelsproj = axs.get_legend_handles_labels()
            axs.legend(handles,labelsproj)
            axs.set_xlabel(r'$m_{%s}$ [GeV]'%projection)
            axs.set_ylabel('Events')
            plt.legend(loc='best')

            syst_type = syst_up.split('_up')[0]
            plt.savefig(f'plots/TemplateSystematics_{setname}_{year}_{region}_{syst_type}_proj{projection}.png')
            plt.savefig(f'plots/TemplateSystematics_{setname}_{year}_{region}_{syst_type}_proj{projection}.pdf')


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='setname',
                        action='store', required=True,
                        help='Setname to process.')
    parser.add_argument('-y', type=str, dest='year',
                        action='store', required=True,
                        help='Year of set (16APV, 16, 17, 18).')
    parser.add_argument('-r', type=str, dest='region',
                        action='store', required=True,
                        help='Analysis region, e.g. "SR_pass"')

    args = parser.parse_args()

    baseFile = 'root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW/selection/XHYbbWWselection_{setname}_{year}{syst}.root'

    plot(args.setname, args.year, args.region)
