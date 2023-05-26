import ROOT
from XHYbbWW_class import XHYbbWW


'''
Simple script to determine how much total efficiency is lost from JetHT dataset when applying different HT cuts to improve trigger efficiency
'''

HT = [1200]
years = [16, 17, 18]

loss = {16: {750: None, 900: None, 1000:None}, 17: {750: None, 900: None, 1000:None}, 18: {750: None, 900: None, 1000:None}}

fName = 'trijet_nano/Data_{}_snapshot.txt'

for year in years:
    selection = XHYbbWW(fName.format(year),year,1,1)
    start = selection.OpenForSelection('None')
    for ht in HT:
	selection.a.SetActiveNode(start)
	before = selection.a.DataFrame.Count().GetValue()
	selection.a.Cut('HT_{}_cut'.format(ht), 'HT > {}'.format(ht))
	after = selection.a.DataFrame.Count().GetValue()
	frac = float(after)/float(before)
	percentage = 100.*frac
	loss[year][ht] = percentage

for year, HTs in loss.items():
    print(year, HTs)
