#include <TFile.h>
#include <TMath.h>
#include <stdio.h>
#include <vector>
#include <iostream>
#include "ROOT/RVec.hxx"
#include "TIMBER/Framework/include/common.h"

using namespace ROOT::VecOps;
using rvec_i = RVec<int>;
using rvec_f = RVec<float>;
using rvec_c = RVec<char>;
using rvec_b = RVec<bool>;

Float_t deltaR(Float_t eta1, Float_t phi1, Float_t eta2, Float_t phi2){
    Float_t deltaEta      = eta2-eta1;
    Float_t deltaPhi_corr = hardware::DeltaPhi(phi1,phi2);//if |phi1-phi2|>pi, reduce it by pi
    Float_t deltaR        = TMath::Sqrt(deltaEta*deltaEta+deltaPhi_corr*deltaPhi_corr);
    return deltaR;
}

Int_t topInJet(Float_t FatJet_phi, Float_t FatJet_eta, Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother, bool returnIdx) {
    for(Int_t i=0; i<nGenPart; i++) {
        Int_t pid = GenPart_pdgId[i];
        Int_t motherIdx = GenPart_genPartIdxMother[i];
        Int_t motherPid = GenPart_pdgId[motherIdx];
        if(motherPid==-1){
            continue;
        }
        Float_t dR = deltaR(GenPart_eta[i],GenPart_phi[i],FatJet_eta,FatJet_phi);
        // look for top quark
        if(TMath::Abs(pid)==6 && dR<0.8){
            if (returnIdx) {return i;}
            else {return 1;}
        }
    }
    if (returnIdx) {return -1;}
    else {return 0;}
};



Int_t higgsInJet(Float_t FatJet_phi, Float_t FatJet_eta, Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother, bool returnIdx) {
    for(Int_t i=0; i<nGenPart; i++) {
        Int_t pid = GenPart_pdgId[i];
        Int_t motherIdx = GenPart_genPartIdxMother[i];
        Int_t motherPid = GenPart_pdgId[motherIdx];
        if(motherPid==-1){
            continue;
        }
        Float_t dR = deltaR(GenPart_eta[i],GenPart_phi[i],FatJet_eta,FatJet_phi);
        // look for higgs
        if (TMath::Abs(pid)==25 && dR<0.8) {
            if (returnIdx) {return i;}
            else {return 1;}
        }
    }
    if (returnIdx) {return -1;} 
    else {return 0;}
};

Int_t wInJet(Float_t FatJet_phi, Float_t FatJet_eta, Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother, bool returnIdx) {
    for(Int_t i=0; i<nGenPart; i++) {
        Int_t pid = GenPart_pdgId[i];
        Int_t motherIdx = GenPart_genPartIdxMother[i];
        Int_t motherPid = GenPart_pdgId[motherIdx];
        if(motherPid==-1){
            continue;
        }
        Float_t dR = deltaR(GenPart_eta[i],GenPart_phi[i],FatJet_eta,FatJet_phi);
        // look for W
        if (TMath::Abs(pid)==24 && dR<0.8) {
            if (returnIdx) {return i;}
            else {return 1;}
        }
    }
    if (returnIdx) {return 0;}
    else {return -1;}
};

// takes the gen match result and gets the index of the matched particle
Int_t get_genpart_idx(Int_t match, Float_t FatJet_phi, Float_t FatJet_eta, Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother) {
    Int_t idx;
    if (match == 0) {
        idx = topInJet(FatJet_phi,FatJet_eta,nGenPart,GenPart_phi,GenPart_eta,GenPart_pdgId,GenPart_genPartIdxMother,true);
        return idx;
    }
    else if (match == 1) {
        idx = wInJet(FatJet_phi,FatJet_eta,nGenPart,GenPart_phi,GenPart_eta,GenPart_pdgId,GenPart_genPartIdxMother,true);
        return idx;
    }
    else if (match == 2) {
        idx = higgsInJet(FatJet_phi,FatJet_eta,nGenPart,GenPart_phi,GenPart_eta,GenPart_pdgId,GenPart_genPartIdxMother,true);
        return idx;
    }
    else if (match == 3) {
        idx = higgsInJet(FatJet_phi,FatJet_eta,nGenPart,GenPart_phi,GenPart_eta,GenPart_pdgId,GenPart_genPartIdxMother,true);
        return idx;
    }
    else {
        return -1;
    }
};

Int_t classifyProbeJet(Int_t fatJetIdx,rvec_f FatJet_phi,rvec_f FatJet_eta, Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother){
    // 0:top, 1:W, 2:H, 3:other, 4:multiple
    Int_t isT = topInJet(FatJet_phi[fatJetIdx],FatJet_eta[fatJetIdx],nGenPart,GenPart_phi,GenPart_eta,GenPart_pdgId,GenPart_genPartIdxMother,false);
    Int_t isW = wInJet(FatJet_phi[fatJetIdx],FatJet_eta[fatJetIdx],nGenPart,GenPart_phi,GenPart_eta,GenPart_pdgId,GenPart_genPartIdxMother,false);
    Int_t isH = higgsInJet(FatJet_phi[fatJetIdx],FatJet_eta[fatJetIdx],nGenPart,GenPart_phi,GenPart_eta,GenPart_pdgId,GenPart_genPartIdxMother,false);

    if ((isT + isW + isH) > 1) {
        // multiple matched particles
        return 4;
    }
    else if ((isT + isW + isH) > 1) {
        // no matched particles
        return 3;
    }
    else {
        if (isT) {
            return 0;
        }
        else if (isW) {
            return 1;
        }
        else if (isH) {
            return 2;
        }
    }
};


RVec<Int_t> classifyProbeJets(RVec<Int_t> fatJetIdxs, rvec_f FatJet_phi,rvec_f FatJet_eta, Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother) {
    RVec<Int_t> out(3);
    for (Int_t iJet : fatJetIdxs) {
        Int_t status = classifyProbeJet(iJet, FatJet_phi, FatJet_eta, nGenPart, GenPart_phi, GenPart_eta, GenPart_pdgId, GenPart_genPartIdxMother);
	out[iJet] = status;
    }
    return out;
}

