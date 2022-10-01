#include "ROOT/RVec.hxx"
#include "TIMBER/Framework/include/common.h"

using namespace ROOT::VecOps;

RVec<int> PickTrijets(RVec<float> pt, RVec<float> eta, RVec<float> phi, RVec<float> mass) {
    // We are looking for a lead jet separated by the two sublead jets by at least 90 degrees
    int jet0Idx = -1;
    int jet1Idx = -1;
    int jet2Idx = -1;
    // Since the vectors are ordered by pT, the first jet should roughly be our Higgs. 
    for (int ijet=0; ijet<pt.size(); ijet++) {
	// this should select the first jet by default, since these criteria have been met with cuts prior to this
	// The mass > 80 should prevent the lead jet from being a W
	if (pt[ijet] > 350 && std::abs(eta[ijet]) < 2.4 && mass[ijet] > 80) {
	    // we've found our lead jet, break loop
	    jet0Idx = ijet;
	    break;
	} 
    }
    // if no lead jet found somehow, return 
    if (jet0Idx == -1) {
	return {-1, -1, -1};
    }
    // now loop over the remaining jets, starting from the index of the lead jet (I'd imagine this would be index 0)
    for (int ijet=jet0Idx; ijet<pt.size(); ijet++) {
	if (hardware::DeltaPhi(phi[jet0Idx], phi[ijet]) > M_PI/2) {
	    jet1Idx = ijet;
	    break;
	}
    }
    // if no sublead jet found, return
    if (jet1Idx == -1) {
	return {-1, -1, -1};
    }
    // now loop over the remaining jets, starting from index of first sublead jet
    for (int ijet=jet1Idx; ijet<pt.size(); ijet++) {
        if (hardware::DeltaPhi(phi[jet0Idx], phi[ijet]) > M_PI/2) {
            jet2Idx = ijet;
            break;
        }
    }
    if (jet2Idx == -1) {
	return {-1, -1, -1};
    }
    else {
	return {jet0Idx, jet1Idx, jet2Idx};
    }
}

