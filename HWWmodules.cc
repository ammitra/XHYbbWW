/**
 * Modules for performing W & H selection for data and non-ttbar/signal MC using
 * only the raw tagger scores.
 */
#include <ROOT/RVec.hxx>
#include <TRandom3.h>
#include <string>
#include <iostream>
#include <stdio.h>
#include <vector>
#include <TFile.h>
#include <TH2F.h>

using namespace ROOT::VecOps;

// New (as of Oct8,2024)
// Returns a vector of indices where first index is idx of jet with highest
// Higgs score, and the second two indices are the remaining idxs (no particular
// order). These two indices will be scanned to ID W candidates
RVec<int> Pick_H_candidate(RVec<float> Hbb_discriminant, RVec<int> idxs) {
    int idx0 = idxs[0];
    int idx1 = idxs[1];
    int idx2 = idxs[2];
    float val0 = Hbb_discriminant[idx0];
    float val1 = Hbb_discriminant[idx1];
    float val2 = Hbb_discriminant[idx2];
    if (val0 >= val1) {
        if (val0 >= val2) {
            return {0,1,2};     // first index is Higgs
        }
        else {
            return {2,0,1};     // first index is Higgs
        }
    }
    else {
        if (val1 >= val2) {
            return {1,0,2};     // first index is Higgs
        }
        else {
            return {2,0,1};     // first index is Higgs
        }
    }
};

// New (as of Oct8,2024)
// Returns a vector of indices corresponding to the (score-ordered) W candidates.
// If either jet does not pass the WP, then return -1 for further analysis.
RVec<int> Pick_W_candidates(RVec<float> Wqq_discriminant, float wp, RVec<int> idxs) {
    int idx0 = idxs[0];
    int idx1 = idxs[1];
    float val0 = Wqq_discriminant[idx0];
    float val1 = Wqq_discriminant[idx1];
    bool isW0 = (val0 >= wp);
    bool isW1 = (val1 >= wp);
    if (isW0 && isW1) { // two candidates are both W-tagged
        if (val0 >= val1) {
            return {idx0, idx1};
        }
        else {
            return {idx1, idx0};
        }
    }
    else { // at least one candidate is not W-tagged
        int status0 = (isW0) ? idx0 : -1;
        int status1 = (isW1) ? idx1 : -1;
        return {status0, status1};
    }
};



// OLD (pre-Oct8,2024) - this was used when picking W candidates before Higgs
RVec<int> Pick_W_candidates_standard(RVec<float> Wqq_discriminant, float wp, bool invert, RVec<int> idxs, float lowerBound) {
    RVec<int> out(3);
    int idx0 = idxs[0];
    int idx1 = idxs[1];
    int idx2 = idxs[2];
    bool isW0, isW1, isW2;
    if (!invert) {      // SIGNAL REGION
        isW0 = (Wqq_discriminant[idx0] >= wp);
        isW1 = (Wqq_discriminant[idx1] >= wp);
        isW2 = (Wqq_discriminant[idx2] >= wp);
    }
    else {              // CONTROL REGION
        isW0 = (Wqq_discriminant[idx0] > lowerBound) && (Wqq_discriminant[idx0] < wp);
        isW1 = (Wqq_discriminant[idx1] > lowerBound) && (Wqq_discriminant[idx1] < wp);
        isW2 = (Wqq_discriminant[idx2] > lowerBound) && (Wqq_discriminant[idx2] < wp);
    }
    // determine which is which
    if (isW0 && isW1 && isW2) { // all 3 jets pass W (anti)tagging - use raw W score to determine "real" W
        if (Wqq_discriminant[idx0] < Wqq_discriminant[idx1]) {
            if (Wqq_discriminant[idx0] < Wqq_discriminant[idx2]) {
                if (Wqq_discriminant[idx1] < Wqq_discriminant[idx2]) {
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
            if (Wqq_discriminant[idx1] < Wqq_discriminant[idx2]) {
                if (Wqq_discriminant[idx0] < Wqq_discriminant[idx2]) {
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
            if (Wqq_discriminant[idx0] > Wqq_discriminant[idx1]) {
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
            if (Wqq_discriminant[idx0] > Wqq_discriminant[idx2]) {
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
            if (Wqq_discriminant[idx1] > Wqq_discriminant[idx2]) {
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
};


int Pick_H_candidate_standard(float Hbb_discriminant, float wp) {
    if (Hbb_discriminant >= wp) {
        return 1;
    }
    else {
        return 0;
    } 
};

