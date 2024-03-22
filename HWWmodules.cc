#include "ROOT/RVec.hxx"
#include "TIMBER/Framework/include/common.h"
#include <stdio.h>
#include <random>

using namespace ROOT::VecOps;

/*
 * PickW with W mass window requirement
 */
RVec<int> PickW_massWindow(RVec<float> WTagger, RVec<int> idxs, RVec<float> massWindow, RVec<float> WMass, float scoreCut, bool invertScore=false) {
    if (idxs.size() > 3) {
	std::cout << "PickW -- WARNING: you have input more than 3 indices. Only 3 indices accepted. Assuming first 3 indices.\n";
    }
    RVec<int> out(3);
    float WP = scoreCut;
    int idx0 = idxs[0];
    int idx1 = idxs[1];
    int idx2 = idxs[2];
    bool isW0, isW1, isW2;
    // Determine which of the jets are Ws
    if (!invertScore) {		// SIGNAL REGION
	isW0 = (WTagger[idx0] > WP) && (WMass[idx0] >= massWindow[0]) && (WMass[idx0] <= massWindow[1]);
        isW1 = (WTagger[idx1] > WP) && (WMass[idx1] >= massWindow[0]) && (WMass[idx1] <= massWindow[1]);
        isW2 = (WTagger[idx2] > WP) && (WMass[idx2] >= massWindow[0]) && (WMass[idx2] <= massWindow[1]);
    }
    else {	// CONTROL REGION - INVERT 
        isW0 = (WTagger[idx0] > 0.05) && (WTagger[idx0] < WP);
        isW1 = (WTagger[idx1] > 0.05) && (WTagger[idx1] < WP);
        isW2 = (WTagger[idx2] > 0.05) && (WTagger[idx2] < WP);
    }
    // Determine output order
    if (isW0 && isW1 && isW2) {		// All 3 jets pass W (anti)tagging
	// There are only 6 permutations, just do them manually..
	// https://pages.mtu.edu/~shene/COURSES/cs201/NOTES/chap03/sort.html
	if (WTagger[idx0] < WTagger[idx1]) {
	    if (WTagger[idx0] < WTagger[idx2]) {
		if (WTagger[idx1] < WTagger[idx2]) {
		    out[0] = idx2;	// highest W score
		    out[1] = idx1;	// middle W score
		    out[2] = idx0;	// lowest W score
		}
		else {
                    out[0] = idx1;
                    out[1] = idx2;
                    out[2] = idx0;
		}
	    }
	    else {
		out[0] = idx1;
		out[1] = idx0;
		out[2] = idx2;
	    }
	}
	else {
	    if (WTagger[idx1] < WTagger[idx2]) {
		if (WTagger[idx0] < WTagger[idx2]) {
		    out[0] = idx2;
		    out[1] = idx0;
		    out[2] = idx1;
		}
		else {
                    out[0] = idx0;
                    out[1] = idx2;
                    out[2] = idx1;
		}
	    }
	    else {
                out[0] = idx0;
                out[1] = idx1;
                out[2] = idx2;
	    }
	}
    }
    // Now check the other two cases (exactly 2 Ws, less than 2 Ws)
    // Since the above logic checks if there are exactly 3 Ws, this will be be true iff there are exactly 2 Ws
    if ( (isW0 && isW1) || (isW0 && isW2) || (isW1 && isW2) ) {	// 0 if less than 2 jets, 1 if 2 jets
	if (isW0 && isW1) { 
	    if (WTagger[idx0] > WTagger[idx1]) {
                out[0] = idx0;
                out[1] = idx1;
                out[2] = idx2;
	    }
	    else {
                out[0] = idx1;
                out[1] = idx0;
                out[2] = idx2;
	    }
	}
	else if (isW0 && isW2) {
	    if (WTagger[idx0] > WTagger[idx2]) {
                out[0] = idx0;
                out[1] = idx2;
                out[2] = idx1;
	    }
	    else {
                out[0] = idx2;
                out[1] = idx0;
                out[2] = idx1;
	    }
	}
	else {
	    if (WTagger[idx1] > WTagger[idx2]) {
                out[0] = idx1;
                out[1] = idx2;
                out[2] = idx0;
	    }
	    else {
                out[0] = idx2;
                out[1] = idx1;
                out[2] = idx0;
	    }
	}
    }
    else {	// less than 2 W jets tagged, return {-1, -1, -1}
	out[0] = -1;
	out[1] = -1;
	out[2] = -1;
    }
    return out;
}

/*
 * The signal region is defined by the presence of two sublead W candidates. This function will
 * identify the location of the Ws in the trijet collection based on their MD_WvsQCD score. If 
 * There are three qualifying W jets, then they will all be ordered in terms of their score. 
 * The output vector will be ordered as followed {LeadW_idx, SubleadW_idx, Higgs_idx}. 
 * If two Ws are not found, the function will return {-1, -1, -1}.
 */ 
RVec<int> PickW(RVec<float> WTagger, RVec<int> idxs, float scoreCut, bool invertScore=false) {
    if (idxs.size() > 3) {
	std::cout << "PickW -- WARNING: you have input more than 3 indices. Only 3 indices accepted. Assuming first 3 indices.\n";
    }
    RVec<int> out(3);
    float WP = scoreCut;
    int idx0 = idxs[0];
    int idx1 = idxs[1];
    int idx2 = idxs[2];
    bool isW0, isW1, isW2;
    // Determine which of the jets are Ws
    if (!invertScore) {		// SIGNAL REGION
	isW0 = (WTagger[idx0] > WP);
        isW1 = (WTagger[idx1] > WP);
        isW2 = (WTagger[idx2] > WP);
    }
    else {	// CONTROL REGION - INVERT 
        isW0 = (WTagger[idx0] > 0.05) && (WTagger[idx0] < WP);
        isW1 = (WTagger[idx1] > 0.05) && (WTagger[idx1] < WP);
        isW2 = (WTagger[idx2] > 0.05) && (WTagger[idx2] < WP);
    }
    // Determine output order
    if (isW0 && isW1 && isW2) {		// All 3 jets pass W (anti)tagging
	// There are only 6 permutations, just do them manually..
	// https://pages.mtu.edu/~shene/COURSES/cs201/NOTES/chap03/sort.html
	if (WTagger[idx0] < WTagger[idx1]) {
	    if (WTagger[idx0] < WTagger[idx2]) {
		if (WTagger[idx1] < WTagger[idx2]) {
		    out[0] = idx2;	// highest W score
		    out[1] = idx1;	// middle W score
		    out[2] = idx0;	// lowest W score
		}
		else {
                    out[0] = idx1;
                    out[1] = idx2;
                    out[2] = idx0;
		}
	    }
	    else {
		out[0] = idx1;
		out[1] = idx0;
		out[2] = idx2;
	    }
	}
	else {
	    if (WTagger[idx1] < WTagger[idx2]) {
		if (WTagger[idx0] < WTagger[idx2]) {
		    out[0] = idx2;
		    out[1] = idx0;
		    out[2] = idx1;
		}
		else {
                    out[0] = idx0;
                    out[1] = idx2;
                    out[2] = idx1;
		}
	    }
	    else {
                out[0] = idx0;
                out[1] = idx1;
                out[2] = idx2;
	    }
	}
    }
    // Now check the other two cases (exactly 2 Ws, less than 2 Ws)
    // Since the above logic checks if there are exactly 3 Ws, this will be be true iff there are exactly 2 Ws
    if ( (isW0 && isW1) || (isW0 && isW2) || (isW1 && isW2) ) {	// 0 if less than 2 jets, 1 if 2 jets
	if (isW0 && isW1) { 
	    if (WTagger[idx0] > WTagger[idx1]) {
                out[0] = idx0;
                out[1] = idx1;
                out[2] = idx2;
	    }
	    else {
                out[0] = idx1;
                out[1] = idx0;
                out[2] = idx2;
	    }
	}
	else if (isW0 && isW2) {
	    if (WTagger[idx0] > WTagger[idx2]) {
                out[0] = idx0;
                out[1] = idx2;
                out[2] = idx1;
	    }
	    else {
                out[0] = idx2;
                out[1] = idx0;
                out[2] = idx1;
	    }
	}
	else {
	    if (WTagger[idx1] > WTagger[idx2]) {
                out[0] = idx1;
                out[1] = idx2;
                out[2] = idx0;
	    }
	    else {
                out[0] = idx2;
                out[1] = idx1;
                out[2] = idx0;
	    }
	}
    }
    else {	// less than 2 W jets tagged, return {-1, -1, -1}
	out[0] = -1;
	out[1] = -1;
	out[2] = -1;
    }
    return out;
}


int getOriginalWCat(float MD_WvsQCD, float WP) {
    if (MD_WvsQCD > WP) {return 1;}    // pass
    else {return 0;}                   // fail
}


float getSF(int jetCat, float pt, std::string _year, int _var) {
    if ((jetCat!=0) && (jetCat!=1)) {std::cerr<<"ERROR - INITIAL JET CATEGORY MUST BE 0 or 1. Current value is " << jetCat << std::endl;}
    // SF[_var][pt] (_var: 0=nom, 1=up, 2=down)
    // variations are described above, pt cats are [200, 300), [300, 400), [400, 800) across all years
    // https://indico.cern.ch/event/1152827/contributions/4840404/attachments/2428856/4162159/ParticleNet_SFs_ULNanoV9_JMAR_25April2022_PK.pdf

    // HP (tight WP)
    float SF2016APV_T[3][3] = {{0.85,0.86,0.86},{0.88,0.90,0.96},{0.82,0.82,0.78}};
    float SF2016_T[3][3]    = {{0.85,0.83,0.69},{0.89,0.87,0.76},{0.81,0.79,0.63}};
    float SF2017_T[3][3]    = {{0.85,0.85,0.86},{0.88,0.88,0.91},{0.82,0.82,0.81}};
    float SF2018_T[3][3]    = {{0.81,0.81,0.77},{0.84,0.83,0.81},{0.78,0.79,0.73}};
    // MP (loose WP)
    float SF2016APV_L[3][3] = {{0.90,0.87,0.92},{0.93,0.91,1.00},{0.87,0.83,0.85}};
    float SF2016_L[3][3]    = {{0.89,0.86,0.73},{0.93,0.90,0.80},{0.86,0.82,0.66}};
    float SF2017_L[3][3]    = {{0.91,0.90,0.89},{0.93,0.93,0.94},{0.89,0.87,0.85}};
    float SF2018_L[3][3]    = {{0.87,0.86,0.82},{0.89,0.88,0.86},{0.85,0.84,0.78}};
    // begin logic
    float SF;
    int ptCat;
    // get the pT category
    if ((pt >= 200) && (pt < 300))	{ ptCat = 0; }
    else if ((pt >= 300) && (pt < 400)) { ptCat = 1; }
    else if ((pt >= 400) && (pt < 800)) { ptCat = 2; }
    else { return 1.0; }
    // get SF
    switch (jetCat) {
	case 0: { // jet originally in fail
            if (_year=="2016APV") { SF = SF2016APV_L[_var][ptCat]; }
            else if (_year=="2016") { SF = SF2016_L[_var][ptCat]; }
            else if (_year=="2017") { SF = SF2017_L[_var][ptCat]; }
            else { SF = SF2018_L[_var][ptCat]; }
	    break;
	}
        case 1: { // jet originally in pass
            if (_year=="2016APV") { SF = SF2016APV_T[_var][ptCat]; }
            else if (_year=="2016") { SF = SF2016_T[_var][ptCat]; }
            else if (_year=="2017") { SF = SF2017_T[_var][ptCat]; }
            else { SF = SF2018_T[_var][ptCat]; }
	    break;
	}
    }
    return SF;
}

double RAND() {
    const double from = 0.0;
    const double to = 1.0;
    std::random_device rand_dev;
    std::mt19937 generator(rand_dev());
    std::uniform_real_distribution<double> distr(from, to);
    return distr(generator);
}

int getNewWCat(float SF, int oldCat, float eff, double rand, bool invert) {
    int newCat = oldCat; // oldCat may be updated, if not then newCat = oldCat
    if (SF < 1) {
	// downgrade fraction (1-SF) of tagged -> untagged
	if ((oldCat == 1) && (rand < 1.-SF)) {
	    newCat=0;
	}
    }
    else {
	// upgrade fraction of untagged -> tagged
	if (oldCat == 0) {
	    float num = 1.-SF;
	    float den = 1.-(1./eff);
	    float f = num/den;
	    if (rand < f) {
		newCat = 1;
	    }
	}
    }
    return newCat;
}

/*
 * The signal region is defined by the presence of two sublead W candidates. This function
 * will identify the location of the Ws in the trijet collection based on their WvsQCD score
 * and then apply SFs and return the indices of the two W jets.
 */
RVec<int> PickWWithSFs(RVec<float> WTagger, 
		RVec<float> HTagger, 
		RVec<float> pt, 
		RVec<int> idxs, 
		float WScoreCut, 
		float eff0, 
		float eff1, 
		float eff2, 
		std::string year, 
		int WVariation, 
		bool invertScore=false) {
    if (idxs.size() > 3) {
	std::cout << "PickW -- WARNING: you have input more than 3 indices. Only 3 accepted. Assuming first three indices.\n";
    }
    RVec<int> out(3);
    float WP = WScoreCut;
    int idx0 = idxs[0];
    int idx1 = idxs[1];
    int idx2 = idxs[2];

    // First, need to determine original tagger categories for each of the three jets
    int orig_score0 = getOriginalWCat(WTagger[idx0], WP);
    int orig_score1 = getOriginalWCat(WTagger[idx1], WP);
    int orig_score2 = getOriginalWCat(WTagger[idx2], WP);
    // Now, determine new tagger category
    float SF0 = getSF(orig_score0, pt[idx0], year, WVariation);
    float SF1 = getSF(orig_score1, pt[idx1], year, WVariation);
    float SF2 = getSF(orig_score2, pt[idx2], year, WVariation);
    if ((SF0==0) || (SF1==0) || (SF2==0)) {std::cerr<<"SF is 0\n";}
    double rand0 = RAND();
    double rand1 = RAND();
    double rand2 = RAND();
    int new_score0 = getNewWCat(SF0, orig_score0, eff0, rand0, invertScore);
    int new_score1 = getNewWCat(SF1, orig_score1, eff1, rand1, invertScore);
    int new_score2 = getNewWCat(SF2, orig_score2, eff2, rand2, invertScore);

    // now perform top selection using the new tagger "scores" (aka categories)
    bool isW0, isW1, isW2;
    if (!invertScore) { // SIGNAL REGION
	isW0 = (new_score0 == 1);
	isW1 = (new_score1 == 1);
	isW2 = (new_score2 == 1);
    }
    else { // CONTROL REGION
	// might have to && some condition for Hbb veto or something. for now, just invert cat
	isW0 = (new_score0 == 0);
	isW1 = (new_score1 == 0);
	isW2 = (new_score2 == 0);
    }
    // determine which is which
    if (isW0 && isW1 && isW2) { // all 3 jets pass W (anti)tagging - use raw W score to determine "real" W
	if (WTagger[idx0] < WTagger[idx1]) {
	    if (WTagger[idx0] < WTagger[idx2]) {
		if (WTagger[idx1] < WTagger[idx2]) {
                    out[0] = idx2;      // highest W score
                    out[1] = idx1;      // middle W score
                    out[2] = idx0;      // lowest W score
		}
		else {
                    out[0] = idx1;
                    out[1] = idx2;
                    out[2] = idx0;
		}
	    }
	}
	else {
            if (WTagger[idx1] < WTagger[idx2]) {
                if (WTagger[idx0] < WTagger[idx2]) {
                    out[0] = idx2;
                    out[1] = idx0;
                    out[2] = idx1;
                }
                else {
                    out[0] = idx0;
                    out[1] = idx2;
                    out[2] = idx1;
                }
            }
            else {
                out[0] = idx0;
                out[1] = idx1;
                out[2] = idx2;
            }
	}
    }
    if ( (isW0 && isW1) || (isW0 && isW2) || (isW1 && isW2) ) { // 0 if less than 2 jets, 1 if 2 jets
        if (isW0 && isW1) {
            if (WTagger[idx0] > WTagger[idx1]) {
                out[0] = idx0;
                out[1] = idx1;
                out[2] = idx2;
            }
            else {
                out[0] = idx1;
                out[1] = idx0;
                out[2] = idx2;
            }
        }
        else if (isW0 && isW2) {
            if (WTagger[idx0] > WTagger[idx2]) {
                out[0] = idx0;
                out[1] = idx2;
                out[2] = idx1;
            }
            else {
                out[0] = idx2;
                out[1] = idx0;
                out[2] = idx1;
            }
        }
        else {
            if (WTagger[idx1] > WTagger[idx2]) {
                out[0] = idx1;
                out[1] = idx2;
                out[2] = idx0;
            }
            else {
                out[0] = idx2;
                out[1] = idx1;
                out[2] = idx0;
            }
        }
    }
    else {      // less than 2 W jets tagged, return {-1, -1, -1}
        out[0] = -1;
        out[1] = -1;
        out[2] = -1;
    }
    return out;
}

/*
 * PickW function for signal, with mass window requirement
 */
RVec<int> PickWWithSFs_massWindow(RVec<float> WTagger,
                RVec<float> HTagger,
                RVec<float> pt,
                RVec<int> idxs,
                RVec<float> WMass,
                RVec<float> massWindow,
                float WScoreCut,
                float eff0,
                float eff1,
                float eff2,
                std::string year,
                int WVariation,
                bool invertScore=false) {
    if (idxs.size() > 3) {
        std::cout << "PickW -- WARNING: you have input more than 3 indices. Only 3 accepted. Assuming first three indices.\n";
    }
    RVec<int> out(3);
    float WP = WScoreCut;
    int idx0 = idxs[0];
    int idx1 = idxs[1];
    int idx2 = idxs[2];

    // First, need to determine original tagger categories for each of the three jets
    int orig_score0 = getOriginalWCat(WTagger[idx0], WP);
    int orig_score1 = getOriginalWCat(WTagger[idx1], WP);
    int orig_score2 = getOriginalWCat(WTagger[idx2], WP);
    // Now, determine new tagger category
    float SF0 = getSF(orig_score0, pt[idx0], year, WVariation);
    float SF1 = getSF(orig_score1, pt[idx1], year, WVariation);
    float SF2 = getSF(orig_score2, pt[idx2], year, WVariation);
    if ((SF0==0) || (SF1==0) || (SF2==0)) {std::cerr<<"SF is 0\n";}
    double rand0 = RAND();
    double rand1 = RAND();
    double rand2 = RAND();
    int new_score0 = getNewWCat(SF0, orig_score0, eff0, rand0, invertScore);
    int new_score1 = getNewWCat(SF1, orig_score1, eff1, rand1, invertScore);
    int new_score2 = getNewWCat(SF2, orig_score2, eff2, rand2, invertScore);

    // now perform top selection using the new tagger "scores" (aka categories)
    bool isW0, isW1, isW2;
    if (!invertScore) { // SIGNAL REGION
        isW0 = (new_score0 == 1) && (WMass[idx0] >= massWindow[0]) && (WMass[idx0] <= massWindow[1]);
        isW1 = (new_score1 == 1) && (WMass[idx1] >= massWindow[0]) && (WMass[idx1] <= massWindow[1]);
        isW2 = (new_score2 == 1) && (WMass[idx2] >= massWindow[0]) && (WMass[idx2] <= massWindow[1]);
    }
    else { // CONTROL REGION
        // might have to && some condition for Hbb veto or something. for now, just invert cat
        isW0 = (new_score0 == 0);
        isW1 = (new_score1 == 0);
        isW2 = (new_score2 == 0);
    }
    // determine which is which
    if (isW0 && isW1 && isW2) { // all 3 jets pass W (anti)tagging - use raw W score to determine "real" W
        if (WTagger[idx0] < WTagger[idx1]) {
            if (WTagger[idx0] < WTagger[idx2]) {
                if (WTagger[idx1] < WTagger[idx2]) {
                    out[0] = idx2;      // highest W score
                    out[1] = idx1;      // middle W score
                    out[2] = idx0;      // lowest W score
                }
                else {
                    out[0] = idx1;
                    out[1] = idx2;
                    out[2] = idx0;
                }
            }
        }
        else {
            if (WTagger[idx1] < WTagger[idx2]) {
                if (WTagger[idx0] < WTagger[idx2]) {
                    out[0] = idx2;
                    out[1] = idx0;
                    out[2] = idx1;
                }
                else {
                    out[0] = idx0;
                    out[1] = idx2;
                    out[2] = idx1;
                }
            }
            else {
                out[0] = idx0;
                out[1] = idx1;
                out[2] = idx2;
            }
        }
    }
    if ( (isW0 && isW1) || (isW0 && isW2) || (isW1 && isW2) ) { // 0 if less than 2 jets, 1 if 2 jets
        if (isW0 && isW1) {
            if (WTagger[idx0] > WTagger[idx1]) {
                out[0] = idx0;
                out[1] = idx1;
                out[2] = idx2;
            }
            else {
                out[0] = idx1;
                out[1] = idx0;
                out[2] = idx2;
            }
        }
        else if (isW0 && isW2) {
            if (WTagger[idx0] > WTagger[idx2]) {
                out[0] = idx0;
                out[1] = idx2;
                out[2] = idx1;
            }
            else {
                out[0] = idx2;
                out[1] = idx0;
                out[2] = idx1;
            }
        }
        else {
            if (WTagger[idx1] > WTagger[idx2]) {
                out[0] = idx1;
                out[1] = idx2;
                out[2] = idx0;
            }
            else {
                out[0] = idx2;
                out[1] = idx1;
                out[2] = idx0;
            }
        }
    }
    else {      // less than 2 W jets tagged, return {-1, -1, -1}
        out[0] = -1;
        out[1] = -1;
        out[2] = -1;
    }
    return out;
}
