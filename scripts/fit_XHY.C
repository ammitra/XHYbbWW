void fit_XHY() {
    TFile f("triggers/HWWtrigger2D_HT0_17.root","READ");
    TEfficiency* eff = (TEfficiency*)f.Get("Pretag");
    TF2* func = new TF2("eff_func","1-[0]/10*exp([1]*y/1000)*exp([2]*x/200)",60,260,800,2600);
    func->SetParameter(0,550);
    func->SetParameter(1,-5);
    func->SetParameter(2,-1);
    TFitResultPtr r = (TFitResultPtr)eff->Fit(func,"SER");
}
