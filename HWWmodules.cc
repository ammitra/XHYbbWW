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

RVec<int> Pick_W_candidates_standard(RVec<float> Wqq_discriminant, float wp, bool invert, RVec<int> idxs) {
    RVec<int> out(3);
    int idx0 = idxs[0];
    int idx1 = idxs[1];
    int idx2 = idxs[2];
    bool isW0, isW1, isW2;
    if (!invert) {      // SIGNAL REGION
        isW0 = (Wqq_discriminant[idx0] > wp);
        isW1 = (Wqq_discriminant[idx1] > wp);
        isW2 = (Wqq_discriminant[idx2] > wp);
    }
    else {              // CONTROL REGION
        isW0 = (Wqq_discriminant[idx0] > 0.05) && (Wqq_discriminant[idx0] < wp);
        isW1 = (Wqq_discriminant[idx1] > 0.05) && (Wqq_discriminant[idx1] < wp);
        isW2 = (Wqq_discriminant[idx2] > 0.05) && (Wqq_discriminant[idx2] < wp);
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

