#include <ROOT/RVec.hxx>
#include <TRandom.h>
#include <string>
#include "TFile.h"
#include "TH2F.h"
#include <iostream>
#include <stdio.h>
#include <vector>
#include <Math/GenVector/LorentzVector.h>
#include <Math/GenVector/PtEtaPhiM4D.h>
#include <Math/Vector4Dfwd.h>
#include "TIMBER/Framework/include/common.h"

using namespace ROOT::VecOps;
using LorentzV = ROOT::Math::PtEtaPhiMVector;

RVec<int> FindMothersPdgId(const ROOT::RVec<int>& genpart_id, const ROOT::RVec<int>& selected_genpart_mother_indices){

    std::size_t Ni = selected_genpart_mother_indices.size();
    RVec<int> mother_pdgids(Ni);    
    for(std::size_t i=0; i<Ni; i++) {
        mother_pdgids[i] = genpart_id[selected_genpart_mother_indices[i]];
    }
    return mother_pdgids;

};

/**
 * Match the FatJets to the generator particles by dR matching
 * 	1: W
 * 	2: H
 * 	3: Top (no merging performed yet)
 */ 
RVec<int> GenMatchingLoop(LorentzV Jet1, LorentzV Jet2, LorentzV Jet3, RVec<float> GenTop_pt, RVec<float> GenTop_eta, RVec<float> GenTop_phi, RVec<float> GenTop_mass, RVec<float> GenW_pt, RVec<float> GenW_eta, RVec<float> GenW_phi, RVec<float> GenW_mass, RVec<float> GenH_pt, RVec<float> GenH_eta, RVec<float> GenH_phi, RVec<float> GenH_mass) {
    RVec<int> out = {-1,-1,-1};
    RVec<LorentzV> jets = {Jet1, Jet2, Jet3};
    int jetCount = 0;
    for (auto jet : jets) {
	bool isW, isH, isTop;
	// check if jet is H/W/top
	for (int iTop=0; iTop<GenTop_pt.size(); iTop++) {
	    LorentzV TopVec(GenTop_pt[iTop], GenTop_eta[iTop], GenTop_phi[iTop], GenTop_mass[iTop]);
	    if (hardware::DeltaR(jet, TopVec) < 0.4) {
		isTop = true;
	    }
	    else {
		isTop = false;
	    }
	}
	for (int iW=0; iW<GenW_pt.size(); iW++) {
            LorentzV WVec(GenW_pt[iW], GenW_eta[iW], GenW_phi[iW], GenW_mass[iW]);
            if (hardware::DeltaR(jet, WVec) < 0.4) {
                isW = true;
            }
            else {
                isW = false;
            }
	}
	for (int iH=0; iH<GenH_pt.size(); iH++) {
            LorentzV HVec(GenH_pt[iH], GenH_eta[iH], GenH_phi[iH], GenH_mass[iH]);
            if (hardware::DeltaR(jet, HVec) < 0.4) {
                isH = true;
            }
            else {
                isH = false;
            }
	}
	//logic to determine which is whihc
	if (isW && !isH && !isTop) {out[jetCount] = 1;}
	else if (!isW && isH && !isTop) {out[jetCount] = 2;}
	else if (!isW && !isH && isTop) {out[jetCount] = 3;}
	else {out[jetCount] = -1;}
	//increment the jet index count
	jetCount++;
    }
    return out;
};
