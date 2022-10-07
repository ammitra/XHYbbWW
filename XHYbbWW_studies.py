import ROOT, time

# don't need to use all of these yet
from TIMBER.Analyzer import HistGroup, Correction
from TIMBER.Tools.Common import CompileCpp

ROOT.gROOT.SetBatch(True)

from XHYbbWW_class import XHYbbWW

# not for use with data
def XHYbbWW_studies(args):
    print('PROCESSING {} {}'.format(args.setname, args.era))
    # ROOT.ROOT.EnableImplicitMT(args.threads)
    start = time.time()

    ##############
    # base setup #
    ##############

    # files are under trijet_nano/setname_era_snapshot.txt
    selection = XHYbbWW('trijet_nano/{}_{}_snapshot.txt'.format(args.setname,args.era),int(args.era) if 'APV' not in args.era else 16,1,1)  # 1/1 jobs
    selection.OpenForSelection('None')
    selection.a.Define('Trijet_vect','hardware::TLvector(Trijet_pt, Trijet_eta, Trijet_phi, Trijet_msoftdrop)')
    selection.a.Define('mhww','hardware::InvariantMass(Trijet_vect)')
    selection.a.Define('m_avg','(Trijet_msoftdrop[0]+Trijet_msoftdrop[1]+Trijet_msoftdrop[2])/3')    # is this necessary?
    # make Lorentz vectors for each of the three jets
    selection.a.Define('H_vect','hardware::TLvector(Trijet_pt[0], Trijet_eta[0], Trijet_phi[0], Trijet_msoftdrop[0])')    # Higgs
    selection.a.Define('LeadW_vect','hardware::TLvector(Trijet_pt[1], Trijet_eta[1], Trijet_phi[1], Trijet_msoftdrop[1])')   # W1
    selection.a.Define('SubleadW_vect','hardware::TLvector(Trijet_pt[2], Trijet_eta[2], Trijet_phi[2], Trijet_msoftdrop[2])')   # W2
    selection.a.Define('Ws_vect','LeadW_vect + SubleadW_vect')	# vector sum of two W vectors 
    # resonance masses
    selection.a.Define('Y','hardware::InvariantMass({LeadW_vect + SubleadW_vect})')
    selection.a.Define('X','hardware::InvariantMass({H_vect + LeadW_vect + SubleadW_vect})')
    selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*{}'.format(selection.GetXsecScale())) # weight

    # tagger definitions

    
    # kinematic definitions
    selection.a.Define('pt0','Trijet_pt[0]')	# Higgs pT
    selection.a.Define('pt1','Trijet_pt[1]')    # Lead W pT
    selection.a.Define('pt2','Trijet_pt[2]')    # Sublead W pT
    selection.a.Define('HT','pt0+pt1+pt2')	# scalar sum of all three Jet pTs, aka hadronic activity pT (not so useful tho)
    selection.a.Define('deltaEta','abs(H_vect.Eta() - Ws_vect.Eta())')   # difference b/w H vector and sum of W vecs
    selection.a.Define('deltaPhi','hardware::DeltaPhi(H_vect.Phi(), Ws_vect.Phi())')
    # get final node to branch off of
    kinOnly = selection.a.Define('deltaY','abs(H_vect.Rapidity() - Ws_vect.Rapidity())')
    
    # kinematic plots
    kinPlots = HistGroup('kinPlots')
    kinPlots.Add('pt0',selection.a.DataFrame.Histo1D(('pt0','Higgs jet pt',100,350,2350),'pt0','weight__nominal'))
    kinPlots.Add('pt1',selection.a.DataFrame.Histo1D(('pt1','Lead W jet pt',100,350,2350),'pt1','weight__nominal'))
    kinPlots.Add('pt2',selection.a.DataFrame.Histo1D(('pt2','Sublead W jet pt',100,350,2350),'pt2','weight__nominal'))
    kinPlots.Add('HT',selection.a.DataFrame.Histo1D(('HT','Scalar sum of pt of HWW jets',150,700,3700),'HT','weight__nominal'))
    kinPlots.Add('deltaEta',selection.a.DataFrame.Histo1D(('deltaEta','| #Delta #eta |',48,0,4.8),'deltaEta','weight__nominal'))
    kinPlots.Add('deltaPhi',selection.a.DataFrame.Histo1D(('deltaPhi','| #Delta #phi |',32,1,3.14),'deltaPhi','weight__nominal'))
    kinPlots.Add('deltaY',selection.a.DataFrame.Histo1D(('deltaY','| #Delta y |',60,0,3),'deltaY','weight__nominal'))
    
    # do N-1 setup, but don't worry about splitting into DAK8 and PN, just use PN
    selection.a.SetActiveNode(kinOnly)   # branch off the kinematic-only node
    # ObjectFromCollection makes a new collection from a derivative collection - specify index
    # at this point, it's important to note that we're just assuming that the Higgs is the leading jet and the two Ws are subleading. 
    selection.a.ObjectFromCollection('Higgs','Trijet',0)
    selection.a.ObjectFromCollection('W1','Trijet',1)
    # now this will be the node we branch off for the N-1 
    nminus1Node = selection.a.ObjectFromCollection('W2','Trijet',2)
    
    # now we can begin the N-1 process
    out = ROOT.TFile.Open('rootfiles/XHYbbWWstudies_{}_{}{}.root'.format(args.setname,args.era,'_'+args.variation if args.variation != 'None' else ''),'RECREATE')
    out.cd()

    # for now, we are only interested in particleNet. But, let's just keep the for loop in case we want to add more
    taggers = ['particleNet']
    for t in taggers:
	higgs_tagger = '{}_HbbvsQCD'.format(t)
        w_tagger = '{}_WvsQCD'.format(t)

	# N-1 - essentially set up mechanics with XHYbbWW.GetNminus1Group() to automate the process via TIMBER -> a.Nminus1()
	selection.a.SetActiveNode(nminus1Node)		# begin at the node returned just before for loop
	nminusGroup = selection.GetNminus1Group(t)	# dictionary of nodes
	print("DEBUG: nminusGroup = {}".format(nminusGroup))
        nminusNodes = selection.a.Nminus1(nminusGroup)	# TIMBER can now be fed the dict and automatically do N-1
	for n in nminusNodes.keys():
	    if n.startswith('m'):    # mass cut
		bins = [25,50,300]
		if n.startswith('mW1'):
		    var = 'W1_msoftdrop'
		elif n.startswith('mW2'):
		    var = 'W2_msoftdrop'
		else:	# we're looking at Higgs
		    var = 'Higgs_msoftdrop'
	    elif n == 'full':   # full cuts, has all N of them
		# this key ALWAYS exists in nminusNodes by default. This is the node which has all of the cuts (that we defined in XHYbbWW_class) applied
                '''
                        |
                    [kinOnly] ---------------------(branch off this for N-2)-----------------
                        |                                                                   |
                       / \                                                           (create new 
                      /   \
                     /     \
                 [cut1]  [cut2]
                  /   \      \
                              \
                               \
                             [cut3] 
                                 \
                                ['full'] <- this is the node with every cut made
                '''
                # this will effectively plot the Y mass (W1+W2) with EVERY other cut that we've defined
		#	- mH, mW1, mW2, H_tag, W1_tag, W2_tag
                # Possible YMasses are 200, 400, 800
                bins = [18,100,1000]   # gives bin width of 50 GeV, removes the lower part w no info, captures the high tail > 900 GeV
                var = 'Y'
	    else:    	# tagger cut
		bins = [50,0,1]
		if n.endswith('H_cut'):
		    var = 'Higgs_{}'.format(higgs_tagger)
		elif n.endswith('W1_cut'):
		    var = 'W1_{}'.format(w_tagger)
		else:	# we're looking at sublead W
		    var = 'W2_{}'.format(w_tagger)
	    print('N-1: Plotting {} for node {}'.format(var, n))
	    if (var == 'Y'):
		kinPlots.Add('YMass_allCuts',nminusNodes[n].DataFrame.Histo1D(('YMass_allCuts','YMass_allCuts',bins[0],bins[1],bins[2]),var,'weight__nominal'))
	    else:
	        kinPlots.Add(n+'_nminus1',nminusNodes[n].DataFrame.Histo1D((n+'_nminus1',n+'_nminus1',bins[0],bins[1],bins[2]),var,'weight__nominal'))

    '''
    EXPERIMENTAL: N-2 plot of Higgs tag cut with everything except the Higgs mass cut
    '''
    selection.a.SetActiveNode(kinOnly)   # branch off the kinematic-only node again (from before N-1 process)
    nminus2Node = nminus1Node    # just return to where N-1 node began 
    taggers = ['particleNet']
    for t in taggers:
	higgs_tagger = '{}_HbbvsQCD'.format(t)
	w_tagger = '{}_WvsQCD'.format(t)
	# get the dict of nodes with XHYbbWW.GetNminus2Group()
	selection.a.SetActiveNode(nminus2Node)		# again get the node returned just after kinematics
	nminus2Group = selection.GetNminus2Group(t)	# returns dict of nodes
	nminus2Nodes = selection.a.Nminus1(nminus2Group)
	# now we want to grab ONLY the key ending with 'H_cut'
	# this key will have all cuts made except the Higgs tagger cut and Higgs mass cut, since we never specified to do the Higgs mass cut in the GetNminus2Group() function
	bins = [50,0,1]
	for n in nminus2Nodes.keys():
	    if n.endswith('H_cut'):
		var = 'Higgs_{}'.format(higgs_tagger)
		print('N-2: Plotting {} for node {} WITHOUT Higgs mass cut'.format(var, n))
		kinPlots.Add(n+'_nminus2',nminus2Nodes[n].DataFrame.Histo1D((n+'_nminus2',n+'_nminus2',bins[0],bins[1],bins[2]),var,'weight__nominal'))
	    else:
		continue

    # now we want to plot mX vs mY for QCD, ttbar, and signal
    MXvsMYPlots = HistGroup('MXvsMYPlots')
    taggers = ['particleNet']
    for t in taggers:
	for W in [[0.3,0.8], [0.8]]:	# plot CR first, then CR
            # Hbb will contain a list of scores on which to vary Hbb: 
	    #	- Region 1 (fail):	Hbb < Hbb[0]
 	    #	- Region 2 (loose):	Hbb[0] < Hbb < Hbb[1]
	    #	- Region 3 (tight):	Hbb > Hbb[1]
	    Hbb = [0.8, 0.98]

	    # W will contain a list of either 1 or two values 
	    # W is chosen in the nested for loop above - we first plot MX vs MY in the CR, then SR
	    print('MX vs MY: Plotting for fail, loose, tight in {}'.format('CR' if len(W)==2 else 'SR'))
            regions = selection.MXvsMY(t, Hbb, W)    # vary Hbb score, apply loose/tight WvsQCD score
	    bins = [60,0,3500]
	    selection.a.SetActiveNode(kinOnly)	# branch off kin-only node again
	    # now that we have the three regions, perform each one 
	    d = {'fail':0, 'loose':1, 'tight':2}
	    for subregion in d.keys():
	        print('Plotting MX vs MY in {} - {}'.format('CR' if len(W)==2 else 'SR', subregion))
	        # start at the kinOnly node
                selection.a.SetActiveNode(nminus1Node)        # so that Trijet subcollection is defined 
	        selection.a.Apply(regions[d[subregion]])      # apply the cutgroup for this region, on the active node (nminus1node)
		# invariant masses X&Y are already defined by the Lorentz vectors H,W1,W2 earlier in the code, so we can just grab them 

		# now we can add the mX vs mY plots to the histgroup. The histos will be named in the format: MXvsMY_<region>_<subregion>
		MXvsMYPlots.Add('MXvsMY_{}_{}'.format('CR' if len(W)==2 else 'SR', subregion), selection.a.DataFrame.Histo2D(('MXvsMY_{}_{}'.format('CR' if len(W)==2 else 'SR',subregion), 'X vs Y Invariant Mass - {} {}'.format('CR' if len(W)==2 else 'SR',subregion), bins[0], bins[1], bins[2], bins[0], bins[1], bins[2]), 'X', 'Y', 'weight__nominal'))

		'''
                # now we can add the mX vs mY plot to the histgroup
	        if (region==0):
	            MXvsMYPlots.Add('MXvsMY_{}_{}'.format(subregion, 'CR' if len(W)==2 else 'SR'),selection.a.DataFrame.Histo2D(('Region{}_MXvsMY'.format(region+1),'X vs Y Invariant Mass (Hbb < {})'.format(Hbb[0]),bins[0],bins[1],bins[2],bins[0],bins[1],bins[2]),'Region{}_X'.format(region+1), 'Region{}_Y'.format(region+1)))
	        elif (region==1):
                    MXvsMYPlots.Add('region{}_MXvsMY'.format(region+1),selection.a.DataFrame.Histo2D(('Region{}_MXvsMY'.format(region+1),'X vs Y Invariant Mass ({0} < Hbb < {1})'.format(*Hbb),bins[0],bins[1],bins[2],bins[0],bins[1],bins[2]),'Region{}_X'.format(region+1), 'Region{}_Y'.format(region+1)))
	        else:
                    MXvsMYPlots.Add('region{}_MXvsMY'.format(region+1),selection.a.DataFrame.Histo2D(('Region{}_MXvsMY'.format(region+1),'X vs Y Invariant Mass (Hbb > {})'.format(Hbb[1]),bins[0],bins[1],bins[2],bins[0],bins[1],bins[2]),'Region{}_X'.format(region+1), 'Region{}_Y'.format(region+1)))
		'''

    print('{} {} Finished'.format(args.setname, args.era))	
    # N-1 loop and N-2 loop are over
    kinPlots.Do('Write')
    MXvsMYPlots.Do('Write')
    selection.a.PrintNodeTree('NodeTree.pdf',verbose=True)
    print('{} sec'.format(time.time() - start))

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='setname',
                        action='store', required=True,
                        help='Setname to process.')
    parser.add_argument('-y', type=str, dest='era',
                        action='store', required=True,
                        help='Year of set (16, 17, 18).')
    parser.add_argument('-v', type=str, dest='variation',
                        action='store', default='None',
                        help='JES_up, JES_down, JMR_up,...')

    args = parser.parse_args()
    XHYbbWW_studies(args)
