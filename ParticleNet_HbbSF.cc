#include<ROOT/RVec.hxx>
#include <TRandom.h>
#include <string>
#include <iostream>
#include <stdio.h>
#include <vector>

/*
 * Class for applying ParticleNet scale factors on a jet-by-jet basis. 
 * For use in the T' -> t\phi analysis, with scale factors located at:
 * https://coli.web.cern.ch/coli/.cms/btv/boohft-calib/20220623_bb_TprimeB_useExpr_2016/4_fit/
 * 
 * Method: https://twiki.cern.ch/twiki/bin/viewauth/CMS/BTagSFMethods#2a_Jet_by_jet_updating_of_the_b
 * There are a few things for consideration:
 *  1) You have to run this for each working point, so that jets that were reassigned for the first WP are used for the second.
 *     To do so, create a new column using TIMBER analyzer's Define() method and pass the new column to the updateTag() method.
 *  2) The efficiencies do not always obey e_hp < e_mp < 1, so this has to be accounted for in the equality check functions.
*/

// NOTE:
// might need to replace this with actual Hbb scale factors (not derived for the Tprime analysis)
using namespace ROOT::VecOps;

class PNetHbbSFHandler {
  private:
    RVec<float> _wps;     // MP [0.8, 0.98], HP [0.98, 1.0]
    RVec<float> _effs;    // efficiencies will be calculated via TIMBER then fed to constructor
    std::string _year;    // 2016APV, 2016, 2017, 2018
    int _var;             // 0: nominal, 1: up, 2: down, passed to constructor
    TRandom _rand;        // used for random number generation
    int _newTags[3]  = {0,0,0};      // number of jets in each new category [fail][loose][tight]
    int _origTags[3] = {0,0,0};      // original num jets in each category [fail][loose][tight]
    
    // SF[_var][pt]
    // variations are described above, pt cats are [400, 600), [600, 800), [800, +inf) across all years
    // HP (tight) [0.98, 1.0]
    float SF2016APV_T[3][3] = {{1.163,1.206,1.491},{1.437,1.529,2.083},{0.949,0.924,0.909}};
    float SF2016_T[3][3]    = {{1.012,1.247,1.188},{1.180,1.509,1.424},{0.899,0.999,0.960}};
    float SF2017_T[3][3]    = {{0.946,1.027,0.900},{1.075,1.158,1.026},{0.830,0.880,0.752}};
    float SF2018_T[3][3]    = {{1.020,1.013,1.082},{1.146,1.110,1.240},{0.894,0.912,0.961}};
    // MP (loose) [0.8, 0.98]
    float SF2016APV_L[3][3] = {{1.102,1.103,0.645},{1.321,1.355,1.914},{0.918,0.871,0.955}};
    float SF2016_L[3][3]    = {{1.032,1.173,1.145},{1.134,1.382,1.332},{0.932,0.970,0.954}};
    float SF2017_L[3][3]    = {{0.973,1.006,1.059},{1.026,1.064,1.132},{0.904,0.931,0.982}};
    float SF2018_L[3][3]    = {{0.904,0.921,1.087},{0.966,0.969,1.165},{0.824,0.841,0.975}};

  public:
    PNetHbbSFHandler(RVec<float> wps, RVec<float> effs, std::string year, int var);  // default: wps={0.8,0.98}, effs={effl,effT}, var=0/1/2
    ~PNetHbbSFHandler();
    int getWPcat(float taggerVal);                                    // determine WP category: 0: fail, 1: loose, 2: tight
    float getSF(float pt, float taggerVal);                           // gets the proper SF based on jet's pt and score as well as internal variables _year, _var
    int updateTag(int jetCat, float pt, float taggerVal);	      // determines the jet's new tagger category
    int createTag(float taggerVal);				      // create new tagger category based on jet's original tagger value
    void printVals();						      // print the number of jets in each category

    // These functions should *NOT* be used, but are included for posterity
    // Essentially, instead of generating a vector of integers, just generate an integer
    // The reason is that we call these via TIMBER's Define() function, which takes in a C++ function or string and applies it to *EVERY* value in the column 
    // This means that we don't have to pass in the vectors themselves, just the column names
    RVec<int> updateTag(RVec<int> jetCats, RVec<float> pt, RVec<float> taggerVals);   // determines the jet's new tagger category 
    RVec<int> createTag(RVec<float> taggerVals);                                      // create vector of tagger categories based on jets' original tagger value.
};

void PNetHbbSFHandler::printVals() {
    // prints the number of original and new tagger values
    printf("Number of Original\n\tFail: %d\n\tLoose: %d\n\tPass: %d\n\tTotal: %d\n", _origTags[0], _origTags[1], _origTags[2], _origTags[0]+_origTags[1]+_origTags[2]);
    printf("Number of New\n\tFail: %d\n\tLoose: %d\n\tPass: %d\n\tTotal: %d\n", _newTags[0], _newTags[1], _newTags[2], _newTags[0]+_newTags[1]+_newTags[2]);
};

PNetHbbSFHandler::PNetHbbSFHandler(RVec<float> wps, RVec<float> effs, std::string year, int var) {
  _wps = wps;
  _effs = effs;
  _year = year;
  _var = var;
  // unique but repeatable random numbers. For repeated calls in the same event, random #s from Rndm() will be identical
  _rand = TRandom(1234);
};

PNetHbbSFHandler::~PNetHbbSFHandler() {
    // print out number of original and new tagger vals upon destruction
    printVals();
};

int PNetHbbSFHandler::getWPcat(float taggerVal) {
  // determine the WP category we're in, 0:fail, 1:loose, 2:tight
  int wpCat;
  if ((taggerVal > _wps[0]) && (taggerVal < _wps[1])) { // loose
    wpCat = 1;
  }
  else if (taggerVal > _wps[1]) { // tight
    wpCat = 2;
  }
  else {  // fail
    wpCat = 0;
  }
  return wpCat;
};

float PNetHbbSFHandler::getSF(float pt, float taggerVal) {
  /* getthe scale factor from the jet's year, score, and pt */
  float SF;
  int ptCat;
  int wpCat = getWPcat(taggerVal);
  // get the pT category
  if ((pt >= 400) && (pt < 600)) {
    ptCat = 0;
  }
  else if ((pt >= 600) && (pt < 800)) {
    ptCat = 1;
  }
  else if (pt > 800) {
    ptCat = 2;
  }
  else {
    // jet is outside of the pt range used in SF derivation, return no change
    return 1.0;
  }
  // get the SF
  switch (wpCat) {
    case 0:   // if jet is originally in fail, pass SF of 1.0 (no change)
      SF = 1.0;
    case 1:   // jet is in MP (loose)
      if (_year=="2016APV") { SF = SF2016APV_L[_var][ptCat]; }
      else if (_year=="2016") { SF = SF2016_L[_var][ptCat]; }
      else if (_year=="2017") { SF = SF2017_L[_var][ptCat]; }
      else { SF = SF2018_L[_var][ptCat]; }
    case 2:   // jet is in HP (tight)
      if (_year=="2016APV") { SF = SF2016APV_T[_var][ptCat]; }
      else if (_year=="2016") { SF = SF2016_T[_var][ptCat]; }
      else if (_year=="2017") { SF = SF2017_T[_var][ptCat]; }
      else { SF = SF2018_T[_var][ptCat]; }
  }
  return SF;
};


int PNetHbbSFHandler::createTag(float taggerVal) {
    /* Creates tagger categories for phi candidate jets
     * this MUST be called in TIMBER before running the rest of the script, as it places all jets into their respective categories for later use in updateTag()
     * This function is meant to be called after selecting the top and higgs in CR and SR (see THselection.py - getEfficiencies)
    */
    if ((taggerVal > _wps[0]) && (taggerVal < _wps[1])) {
	_origTags[1]++;
	return 1;
    }
    else if (taggerVal > _wps[1]) {
	_origTags[2]++;
	return 2;
    }
    else {
	_origTags[0]++;
	return 0;
    }
};

int PNetHbbSFHandler::updateTag(int jetCat, float pt, float taggerVal) {
    /* updates the tagger category for phi jets
     * https://twiki.cern.ch/twiki/bin/view/CMS/BTagSFMethods#2a_Jet_by_jet_updating_of_the_b
     * Params:
     * 	 jetCat    = original jet category (0: fail, 1: loose, 2: pass)
     * 	 pt        = jet pt
     * 	 taggerVal = particleNet tagger value
    */ 
    float eff_L = _effs[0];
    float eff_T = _effs[1];
    float SF_L = getSF(pt, taggerVal);
    float SF_T = getSF(pt, taggerVal);
    double rn = _rand.Rndm();
    int newCat = jetCat;	// grab the original tag category, will be updated
    // begin logic
    if ((SF_L < 1) && (SF_T < 1)) {
	if ( (newCat==2) && (rn < (1.-SF_T)) ) newCat=0;	// tight (2) -> untag (0)
	if ( (newCat==1) && (rn < (1.-SF_L)) ) newCat=0;	// loose (1) -> untag (0)
    }
    if ((SF_L > 1) && (SF_T > 1)) {
	float fL, fT;
	if (newCat==0) {
	    float num = eff_T*(SF_T-1.);
	    float den = 1.-(eff_L+eff_T);
	    fT = num/den;
	    if (rn < fT) newCat=2;	// untag (0) -> tight (2)
	    else {
		rn = _rand.Rndm();
		num = eff_L*(SF_L-1.);
		den = (1.-eff_L-eff_T)*(1.-fT);
		fL = num/den;
		if (rn < fL) newCat=1; 	// loose (1) -> tight (2)
	    }
	}
    }
    if ((SF_L < 1) && (SF_T > 1)) {
	if (newCat==0) {
	    float num = eff_T*(SF_T-1.);
	    float den = 1.-(eff_L+eff_T);
	    float f = num/den;
	    if (rn < f) newCat=2;	    // untag (0) -> tight (2)
	}
	if (newCat==1) {
	    if (rn < (1.-SF_L)) newCat=0;   // loose (1) -> untag (0)
	}
    }
    if ((SF_L > 1) && (SF_T < 1)) { 
	if ((newCat==2) && (rn < (1.-SF_T))) newCat=0;	// tight (2) -> untag (0)
	if (newCat==0) {
	    float num = eff_L*(SF_L-1.);
	    float den = 1.-(eff_L+eff_T);
	    float f = num/den;
	    if (rn < f) newCat=1;	// untag (0) -> loose (1)
	}
    }
    // update the new tag category array
    _newTags[newCat]++;
    // return the new tagger category value
    return newCat;
};
