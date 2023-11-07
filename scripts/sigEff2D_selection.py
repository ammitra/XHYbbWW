import ROOT
import glob
from array import array
import numpy as np
import matplotlib
import matplotlib as mpl
import matplotlib.pyplot as plt
from collections import OrderedDict
import subprocess

mY = OrderedDict([(i,None) for i in [60,70,80,90,100,125,150,190,250,300,350,400,450,500,600,700,800,900,1000,1100,1200,1300,1400,1600,1800,2000,2200,2400,2500,2600,2800]])

redirector = 'root://cmsxrootd.fnal.gov/'
eos_path = '/store/user/ammitra/XHYbbWW/selection/'

def GetEfficiencies(year):
    efficiencies = OrderedDict([(i,mY.copy()) for i in [240,280,300,320,360,400,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2200,2400,2500,2600,2800,3000,3500,4000]])
    
