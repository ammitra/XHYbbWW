import ROOT

def drawHist(hist, can):
    c.Clear()
    c.cd()
    c.Divide(2,1)
    c.cd(1)
    hist.Draw("colz")
    c.cd(2)
    hist.Draw("lego2")
    c.Print("plots/check_RPF.pdf")

hNames = ['Data R_{L/F}','Data R_{P/L}','Data R_{P/F}','Data R_{L/F} smooth','Data R_{P/L} smooth']

f = ROOT.TFile.Open("rootfiles/RPF_data.root",'READ')
c = ROOT.TCanvas('c','c',800,500)
c.Print('plots/check_RPF.pdf[')
c.Clear()
for hName in hNames:
    print('opening {}'.format(hName))
    print(f.Get(hName))
    drawHist(f.Get(hName),c)
c.Print('plots/check_RPF.pdf]')
