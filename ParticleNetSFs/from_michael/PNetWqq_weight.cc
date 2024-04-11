#include "TFile.h"
#include "TH2F.h"
#include <ROOT/RVec.hxx>
#include <string>
#include <set>
#include <algorithm>
#include <math.h>
//#include "common.h"

/**
 * C++ class to handle the application of ParticleNet MD_Wqq scale factors.
 */
class PNetWqq_weight {
    private:
	std::string _effmapname;	// name of the efficiency map ROOT file
	std::string _year;		// "16", "16APV", "17", "18"
	TFile * _effroot;		// pointer to the efficiency map file
	TH2F * _effmap;			// pointer to the efficiency map histo
	float _wp;			// Wqq working point to distinguish pass/fail (e.g. 0.8)
        int _target_flavor;             // Flavor for SF application (0: top, 1: W, 2: bq, 3: unmerged, -1 "other" (variable))
        std::set<int> _other;           // Jet flavors which constitute the "other" category for SF application

        // https://indico.cern.ch/event/1152827/contributions/4840404/attachments/2428856/4162159/ParticleNet_SFs_ULNanoV9_JMAR_25April2022_PK.pdf
    	// SF[pt][var]

        //Top SF, pt cats: [300,450), [450,600), [600,+inf)
	std::vector<std::vector<float>> SF2016APV_t = {{0.992,1.055,0.929},{0.972,1.029,0.915},{1.002,1.103,0.902}};
	std::vector<std::vector<float>> SF2016_t = {{0.839,0.907,0.773},{1.001,1.062,0.941},{1.048,1.144,0.956}};
	std::vector<std::vector<float>> SF2017_t = {{1.100,1.160,1.041},{1.027,1.070,0.985},{1.154,1.221,1.087}};
	std::vector<std::vector<float>> SF2018_t = {{1.055,1.094,1.017},{1.015,1.046,0.984},{0.967,1.025,0.911}};

        //W SF, pt cats: [300,450), [450,600), [600,+inf)
	std::vector<std::vector<float>> SF2016APV_w = {{1.004,1.091,0.928},{1.247,1.425,1.103},{0.723,0.952,0.546}};
	std::vector<std::vector<float>> SF2016_w = {{1.035,1.160,0.933},{0.869,1.003,0.758},{1.301,1.696,1.014}};
	std::vector<std::vector<float>> SF2017_w = {{1.019,1.101,0.947},{0.800,0.847,0.756},{0.877,1.018,0.750}};
	std::vector<std::vector<float>> SF2018_w = {{0.784,0.829,0.743},{0.783,0.826,0.743},{0.755,0.855,0.670}};

        //"Other" SF, pt cats: [300,450), [450,600), [600,+inf)
	std::vector<std::vector<float>> SF2016APV_o = {{1.025,1.060,0.990},{1.024,1.070,0.978},{1.242,1.333,1.152}};
	std::vector<std::vector<float>> SF2016_o = {{0.988,1.026,0.950},{0.968,1.015,0.921},{1.008,1.104,0.915}};
	std::vector<std::vector<float>> SF2017_o = {{1.016,1.054,0.979},{1.191,1.228,1.155},{1.192,1.260,1.127}};
	std::vector<std::vector<float>> SF2018_o = {{1.080,1.111,1.049},{1.125,1.154,1.096},{1.270,1.329,1.212}};


	float GetMCEfficiency(float pt, float eta, int flavor);	// get the efficiency from efficiency map based on jet's pT and eta
	std::vector<float> GetScaleFactors(float pt, int flavor);	// get the scale factor based on pT bin and internal year + SF variation (0=nominal, 1=up, 2=down)

    public:
	PNetWqq_weight(std::string year, std::string effmapname, std::string histname, float wp, int target_flavor, std::set<int> other = {2,3}); // pass in year and path of eff map
	~PNetWqq_weight();

	// Return a vector of weights for each event: {nom,up,down}
	RVec<float> eval(float Wqq_pt, float Wqq_eta, float Wqq_PNetWqqScore, int Wqq_jetFlavor);	

};

// Constructor - set year and load eff map in memory, 
PNetWqq_weight::PNetWqq_weight(std::string year, std::string effmapname, std::string histname, float wp, int target_flavor, std::set<int> other):_effmapname(effmapname),_year(year),_wp(wp),_target_flavor(target_flavor),_other(other) {
    // I am assuming that it is one ROOT file per year, with one histogram.
    _effroot = TFile::Open(_effmapname.c_str(),"READ");//hardware::Open(_effmapname, false);
    _effmap = (TH2F*)_effroot->Get(histname.c_str());
};

// Close files on destruction
PNetWqq_weight::~PNetWqq_weight() {
    _effroot->Close();
};

// Get the MC effieciency of the jets in the given (pT, eta) bin
float PNetWqq_weight::GetMCEfficiency(float pt, float eta, int flavor) {
    // Efficiency map binned in pT: [60,0,3000], eta: [24,-2.4,2.4]
    int xbin = (int)(pt*30./3000.);
    int ybin = (int)((eta+2.4)*24/4.8);
    return _effmap->GetBinContent(xbin,ybin);
};

// Get the SF for the jet based on its pT and score and (internal) variation
std::vector<float> PNetWqq_weight::GetScaleFactors(float pt, int flavor) {
    // First check which pT bin we're in
    int ptBin;
    if (pt >= 300 && pt <= 450) {ptBin = 0;}
    else if (pt > 450 && pt <= 600) {ptBin = 1;}
    else if (pt > 600) {ptBin = 2;}

    std::vector<float> SF;
    if (flavor != _target_flavor) {
        if (_target_flavor == -1 && _other.count(flavor)) {
            if (_year == "16") {SF = SF2016_o[ptBin];}
            else if (_year == "16APV") {SF = SF2016APV_o[ptBin];}
            else if (_year == "17") {SF = SF2017_o[ptBin];}
            else {SF = SF2018_o[ptBin];}
        }
        else {
            SF = {1,1,1};
        }
    }
    else {
	if (flavor == 1) {	// SFs for Wqq
	    if 	    (_year == "16") {SF = SF2016_w[ptBin];}
	    else if (_year == "16APV") {SF = SF2016APV_w[ptBin];}
	    else if (_year == "17") {SF = SF2017_w[ptBin];}
	    else {SF = SF2018_w[ptBin];}
	}
	else if (flavor == 0) {	// SFs for top merged
            if      (_year == "16") {SF = SF2016_t[ptBin];}
            else if (_year == "16APV") {SF = SF2016APV_t[ptBin];}
            else if (_year == "17") {SF = SF2017_t[ptBin];}
            else {SF = SF2018_t[ptBin];}	    
	}
	else {
	    SF = {1,1,1};
	}
    }
    return SF;
    /*
    // Check if selecting scale factor for "other" jets
    if (flavor != _target_flavor) {
        if (_target_flavor == -1 && _other.count(flavor)) {
            if (_year == "16") {SF = SF2016_o[ptBin][variation];}
            else if (_year == "16APV") {SF = SF2016APV_o[ptBin][variation];}
            else if (_year == "17") {SF = SF2017_o[ptBin][variation];}
            else {SF = SF2018_o[ptBin][variation];}
        }
        else {
            SF = 1;
        }
    }  
    else {
        if (flavor == 0) { // Get medium working point SF for merged top jet
            if (_year == "16") {SF = SF2016_t[ptBin][variation];}	
            else if (_year == "16APV") {SF = SF2016APV_t[ptBin][variation];}       
            else if (_year == "17") {SF = SF2017_t[ptBin][variation];}       
            else {SF = SF2018_t[ptBin][variation];}
        }

        else if (flavor == 1) { // Get medium working point SF for merged w jet
            if (_year == "16") {SF = SF2016_w[ptBin][variation];}
            else if (_year == "16APV") {SF = SF2016APV_w[ptBin][variation];}
            else if (_year == "17") {SF = SF2017_w[ptBin][variation];}
            else {SF = SF2018_w[ptBin][variation];}
        }
   
        else {SF = 1;}
    }
    return SF;
    */
};

RVec<float> PNetWqq_weight::eval(float Wqq_pt, float Wqq_eta, float Wqq_PNetWqqScore, int Wqq_jetFlavor) {
    // Prepare the vector of weights to return
    RVec<float> out(3);
    float WqqTagEventWeight;
    float eff;
    std::vector<float> SF;
    SF = GetScaleFactors(Wqq_pt, Wqq_jetFlavor);
    eff = GetMCEfficiency(Wqq_pt, Wqq_eta, Wqq_jetFlavor);
    std::cout << "---------------- New Event ----------------------------\n";
    for (int i : {0,1,2}) {
	float MC_tagged = 1.0, MC_notTagged = 1.0;
	float data_tagged = 1.0, data_notTagged = 1.0;
	std::cout << "SF: " << SF[i] << "\n";
	std::cout << "score: " << Wqq_PNetWqqScore << "\n";
	std::cout << "wp :" << _wp << "\n";
	if (Wqq_PNetWqqScore > _wp) {
	    data_tagged *= SF[i];
	}
	else {
	    if (eff == 1) {eff = 0.99;}
	    MC_notTagged *= (1. - eff);
	    data_notTagged *= (1. - SF[i]*eff);
	}
	WqqTagEventWeight = (data_tagged*data_notTagged) / (MC_tagged*MC_notTagged);
	out[i] = WqqTagEventWeight;
	std::cout << "eff: " << eff << " var: " << i << " weight: " << WqqTagEventWeight << "\n";
    }
    return out;

    /*
    // Loop over variations (0:nom, 1:up, 2:down)
    for (int var : {0,1,2}) {
	// these are for Wqq tagging SFs
	float MC_tagged = 1.0,  MC_notTagged = 1.0;
        float data_tagged = 1.0, data_notTagged = 1.0;

	float WqqTagEventWeight; // final multiplicative factor
        float SF, eff;    // SF(pt,score), eff(pt, eta)
        // get SF and MC efficiency for this particular jet
        SF = GetScaleFactor(Wqq_pt, Wqq_jetFlavor, var);
        eff = GetMCEfficiency(Wqq_pt, Wqq_eta, Wqq_jetFlavor);
        if (Wqq_PNetWqqScore > _wp) {  // PASS
            //MC_tagged *= eff;
            //data_tagged *= SF*eff;
            data_tagged *= SF;
        }
        else {  // FAIL
            if (eff == 1) {eff = 0.99;} // Prevent the event weight from becoming undefined
            MC_notTagged *= (1 - eff);
            data_notTagged *= (1 - SF*eff);
        }
        // Calculate the event weight for this variation
        WqqTagEventWeight = (data_tagged*data_notTagged) / (MC_tagged*MC_notTagged);
        out[var] = WqqTagEventWeight;

    } // end loop over variations

    // Send it {weight_nom, weight_up, weight_down}
    return out;
    */
};
