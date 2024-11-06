#include <TRandom3.h>
#include <iostream>
#include <string>

using namespace Pythonic;
using namespace ROOT::VecOps;

/**
 * Class to perform the HEM veto required for 2018 data and MC. Details here: https://indico.cern.ch/event/1466604/#7-jme-contact-report
 * For data, the conditions for veto are any jet with: 
 *      Run >= 319077
 *      -3.2 < eta < -1.3
 *      -1.57 < phi < -0.87 
 *
 * For MC, the condition for veto is to veto jets in the HEM area in ~65% of UL18 MC events
 */
class HEM_veto {
    private:
        bool _isData;
        std::string _setname;
        TRandom3*   _rand;
    public:
        HEM_veto(std::string setname);
        ~HEM_veto();
        int eval(RVec<float> FatJet_eta, RVec<float> FatJet_phi, int run);
};

HEM_veto::HEM_veto(std::string setname) : _isData(InString("Data",setname)), _setname(setname) {
    _rand = new TRandom3(12345);
};

HEM_veto::~HEM_veto() {
    delete _rand;
};

int HEM_veto::eval(RVec<float> FatJet_eta, RVec<float> FatJet_phi, int run) {
    int drop = 0;
    // First check if there is a jet in the affected region 
    for (size_t i=0; i<FatJet_eta.size(); i++) {
        if ( (FatJet_eta[i] > -3.2) && (FatJet_eta[i] < -1.3) && (FatJet_phi[i] > -1.57) && (FatJet_phi[i] < -0.87) ) {
            // Veto differently in data vs MC 
            if (_isData) {
                if (run >= 319077) {
                    //std::cout << "Jet with run >= 319077 in HEM region (" << FatJet_eta[i] << ", " << FatJet_phi[i] << ") - VETOING" << std::endl;
                    drop = 1;
                    break;
                }
            }// end if Data
            else {
                float rand = _rand->Uniform(1.0);
                if (rand < 0.65) {
                    drop = 1;
                    break;
                }
            }// end if MC
        }// end if jet affected
    }// end loop over jets
    return drop;
};

