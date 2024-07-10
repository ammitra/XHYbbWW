#include <ROOT/RVec.hxx>
#include <TRandom3.h>
#include <string>
#include <vector>
#include <TFile.h>
#include <TH2F.h>
#include <TEfficiency.h>

using namespace ROOT::VecOps;

class PNetMDWSF_weight {
    private:
        // Internal variables
        std::string _year;      // "16", "16APV", "17", "18"
        std::string _category;  // "signal", "ttbar" - applying TAGGING SFs to singal, MISTAGGING SFs to ttbar
        TFile*      _effroot;   // store pointer to efficiency file
        float _wp;              // PNet Hbb tagger working point
        // W tagging scale factors ------------------------------------------------------------------------
        // pt categories: [200, 300), [300, 400), [400, +inf)           {nom, up, down}
        std::vector<std::vector<float>> SF2016APV = {{0.90,0.93,0.87},{0.87,0.91,0.83},{0.86,0.94,0.78}};
        std::vector<std::vector<float>> SF2016    = {{0.89,0.93,0.86},{0.86,0.90,0.82},{0.73,0.80,0.64}};
        std::vector<std::vector<float>> SF2017    = {{0.91,0.93,0.89},{0.90,0.93,0.87},{0.89,0.94,0.85}};
        std::vector<std::vector<float>> SF2018    = {{0.87,0.89,0.85},{0.86,0.88,0.84},{0.82,0.86,0.78}};
        // top mistagging scale factors -------------------------------------------------------------------
        // pt categories: [300,450), [450,600), [600,+inf)              {nom, up, down}
        // TOP MERGED : bqq
        std::vector<std::vector<float>> SF2016APV_t = {{0.992,1.055,0.929},{0.972,1.029,0.915},{1.002,1.103,0.902}};
        std::vector<std::vector<float>> SF2016_t    = {{0.839,0.907,0.773},{1.001,1.062,0.941},{1.048,1.144,0.956}};
        std::vector<std::vector<float>> SF2017_t    = {{1.100,1.160,1.041},{1.027,1.070,0.985},{1.154,1.221,1.087}};
        std::vector<std::vector<float>> SF2018_t    = {{1.055,1.094,1.017},{1.015,1.046,0.984},{0.967,1.025,0.911}};
        // W MERGED : qq
        std::vector<std::vector<float>> SF2016APV_w = {{1.004,1.091,0.928},{1.247,1.425,1.103},{0.723,0.952,0.546}};
        std::vector<std::vector<float>> SF2016_w    = {{1.035,1.160,0.933},{0.869,1.003,0.758},{1.301,1.696,1.014}};
        std::vector<std::vector<float>> SF2017_w    = {{1.019,1.101,0.947},{0.800,0.847,0.756},{0.877,1.018,0.750}};
        std::vector<std::vector<float>> SF2018_w    = {{0.784,0.829,0.743},{0.783,0.826,0.743},{0.755,0.855,0.670}};
        // OTHER:
        std::vector<std::vector<float>> SF2016APV_o = {{1.025,1.060,0.990},{1.024,1.070,0.978},{1.242,1.333,1.152}};
        std::vector<std::vector<float>> SF2016_o    = {{0.988,1.026,0.950},{0.968,1.015,0.921},{1.008,1.104,0.915}};
        std::vector<std::vector<float>> SF2017_o    = {{1.016,1.054,0.979},{1.191,1.228,1.155},{1.192,1.260,1.127}};
        std::vector<std::vector<float>> SF2018_o    = {{1.080,1.111,1.049},{1.125,1.154,1.096},{1.270,1.329,1.212}};
        // Helper functions
        int   GetPtBin(float pt);
        float GetSF(float pt, int variation, int jetCat);
        float GetEff(float pt, float eta, int jetCat);
    public:
        PNetMDWSF_weight(std::string year, std::string category, std::string effpath, float wp);
        ~PNetMDWSF_weight();
        RVec<float> eval(RVec<float> pt, RVec<float> eta, RVec<float> PNetWqq_score, RVec<int> jetCat);
};

PNetMDWSF_weight::PNetMDWSF_weight(std::string year, std::string category, std::string effpath, float wp) : _year(year), _category(category), _wp(wp) {
    _effroot = TFile::Open(effpath.c_str(), "READ");
};

PNetMDWSF_weight::~PNetMDWSF_weight() {
    _effroot->Close();
};

int PNetMDWSF_weight::GetPtBin(float pt) {
    // pT binning differs for signal and mistagging SFs - handle that here
    int ptBin;
    if (_category == "signal") {        // PNet Hbb tagging SFs
        if      (pt >= 200 && pt < 300) { ptBin=0; }
        else if (pt >= 300 && pt < 400) { ptBin=1; }
        else if (pt >= 400) { ptBin=2; }
        else    { ptBin = 0; }
    }
    else if (_category == "ttbar") {    // PNet Hbb mistagging SFs
        if      (pt >= 300 && pt < 450) { ptBin=0; }
        else if (pt >= 450 && pt < 600) { ptBin=1; }
        else if (pt >= 600) { ptBin=2; }
        else    { ptBin = 0; }
    }
    return ptBin;
};

float PNetMDWSF_weight::GetSF(float pt, int variation, int jetCat) {
    // Obtain the SF for this jet based on whether we are handling signal or ttbar
    float SF;
    int ptBin = GetPtBin(pt);
    int var   = variation;   // 0:nom, 1:up, 2:down
    // only used for ttbar:
    // 0:other, 1: qq, 2: bq, 3:bqq
    if (_category == "signal") {
        if (_year == "16APV") {
            SF = SF2016APV[ptBin][var];
        }
        else if (_year == "16") {
            SF = SF2016[ptBin][var];
        }
        else if (_year == "17") {
            SF = SF2017[ptBin][var];
        }
        else {
            SF = SF2018[ptBin][var];
        }
    }
    else if (_category == "ttbar") {        // we only want to apply mistagging SFs to ttbar in SR/CR
        if (_year == "16APV") {
            if (jetCat == 0) {
                SF = 1.0;//= SF2016APV_o[ptBin][var];
            }
            else if (jetCat == 1) {
                SF = SF2016APV_w[ptBin][var];
            }
            else if (jetCat == 2) {
                SF = SF2016APV_w[ptBin][var];
            }
            else if (jetCat == 3) {
                SF = SF2016APV_t[ptBin][var];
            }
            else {
                SF = 1.0;
            }
        }
        else if (_year == "16") {
            if (jetCat == 0) {
                SF = 1.0;//= SF2016_o[ptBin][var];
            }
            else if (jetCat == 1) {
                SF = SF2016_w[ptBin][var];
            }
            else if (jetCat == 2) {
                SF = SF2016_w[ptBin][var];
            }
            else if (jetCat == 3) {
                SF = SF2016_t[ptBin][var];
            }
            else {
                SF = 1.0;
            }
        }
        else if (_year == "17") {
            if (jetCat == 0) {
                SF = 1.0;//= SF2017_o[ptBin][var];
            }
            else if (jetCat == 1) {
                SF = SF2017_w[ptBin][var];
            }
            else if (jetCat == 2) {
                SF = SF2017_w[ptBin][var];
            }
            else if (jetCat == 3) {
                SF = SF2017_t[ptBin][var];
            }
            else {
                SF = 1.0;
            }
        }
        else {
            if (jetCat == 0) {
                SF = 1.0;//= SF2018_o[ptBin][var];
            }
            else if (jetCat == 1) {
                SF = SF2018_w[ptBin][var];
            }
            else if (jetCat == 2) {
                SF = SF2018_w[ptBin][var];
            }
            else if (jetCat == 3) {
                SF = SF2018_t[ptBin][var];
            }
            else {
                SF = 1.0;
            }
        }
    }
    return SF;
};

float PNetMDWSF_weight::GetEff(float pt, float eta, int jetCat) {
    // Obtain the efficiency for the given jet based on its top merging category (if ttbar) or H matching if signal
    // Efficiency map binned in pT: [60,0,3000], eta: [12,-2.4,2.4]
    float eff;
    TEfficiency* _effmap;
    // only used for ttbar:
    // 0:other, 1: qq, 2: bq, 3:bqq
    int cat = jetCat;

    if (_category == "signal") {
        // NOTE: for the gen matching, the "real" Ws (not from top) are actually called 'top_qq-matched', so just use that for the W-tagging eff
        //_effmap = (TEfficiency*)_effroot->Get("W-matched_Trijet_particleNetMD_WvsQCD_WP0p8_TEff");
        _effmap = (TEfficiency*)_effroot->Get("top_qq-matched_Trijet_particleNetMD_WvsQCD_WP0p8_TEff");
    }
    else if (_category == "ttbar") {
        if (cat == 0) {
            _effmap = (TEfficiency*)_effroot->Get("other-matched_Trijet_particleNetMD_WvsQCD_WP0p8_TEff");
        }
        else if (cat == 1) {
            _effmap = (TEfficiency*)_effroot->Get("top_qq-matched_Trijet_particleNetMD_WvsQCD_WP0p8_TEff");
        }
        else if (cat == 2) {
            _effmap = (TEfficiency*)_effroot->Get("top_bq-matched_Trijet_particleNetMD_WvsQCD_WP0p8_TEff");
        }
        else if (cat == 3) {
            _effmap = (TEfficiency*)_effroot->Get("top_bqq-matched_Trijet_particleNetMD_WvsQCD_WP0p8_TEff");
        }
        else { // 4, 5 correspond to Higgs, W (not from top), so just make these other?
            _effmap = (TEfficiency*)_effroot->Get("other-matched_Trijet_particleNetMD_WvsQCD_WP0p8_TEff");
        }
    }

    int globalbin = _effmap->FindFixBin(pt, eta);
    eff = _effmap->GetEfficiency(globalbin);
    delete _effmap;
    return eff;
};

RVec<float> PNetMDWSF_weight::eval(RVec<float> pt, RVec<float> eta, RVec<float> PNetWqq_score, RVec<int> jetCat) {
    RVec<float> out(3);
    for (int var : {0,1,2}) {
        float MC_tagged = 1.0, MC_notTagged = 1.0;
        float data_tagged = 1.0, data_notTagged = 1.0;
        float PNetWqq_event_weight;
        for (int i=0; i<pt.size(); i++) {
            float SF, eff;
            SF  = GetSF(pt[i], var, jetCat[i]);
            eff = GetEff(pt[i], eta[i], jetCat[i]);
            if (PNetWqq_score[i] > _wp) {
                MC_tagged *= eff;
                data_tagged *= SF*eff;
            }
            else {
                MC_notTagged *= (1.-eff);
                data_notTagged *= (1.-SF*eff);
            }
        }
        if ( (MC_tagged * MC_notTagged) == 0.0 ) {
            PNetWqq_event_weight = 1.0;
        }
        else {
            PNetWqq_event_weight = (data_tagged * data_notTagged) / (MC_tagged * MC_notTagged);
        }
        out[var] = PNetWqq_event_weight;
    }
    return out;
};

