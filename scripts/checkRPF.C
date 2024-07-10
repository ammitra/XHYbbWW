void drawHists(TH2D* hist, TCanvas* c) {
    std::cout << "entered printing loop\n";
    c->Clear();
    c->cd();
    c->Divide(2,1); // colz and lego
    c->cd(1);
    hist->Draw("colz");
    c->cd(2);
    hist->Draw("lego2");
    c->Print("plots/check_RPF.pdf");
}

void checkRPF() {
    // Open files
    TFile *fData = TFile::Open("rootfiles/XHYbbWWselection_HT0_Data_Run2.root","READ");
    TFile *fTTbar = TFile::Open("rootfiles/XHYbbWWselection_HT0_ttbar_Run2.root","READ");
    // Get histos
    TH2D *hDF = (TH2D*)fData->Get("MXvMY_particleNet_CR_fail__nominal");
    TH2D *hDL = (TH2D*)fData->Get("MXvMY_particleNet_CR_loose__nominal");
    TH2D *hDP = (TH2D*)fData->Get("MXvMY_particleNet_CR_pass__nominal");
    TH2D *hTTF = (TH2D*)fTTbar->Get("MXvMY_particleNet_CR_fail__nominal");
    TH2D *hTTL = (TH2D*)fTTbar->Get("MXvMY_particleNet_CR_loose__nominal");
    TH2D *hTTP = (TH2D*)fTTbar->Get("MXvMY_particleNet_CR_pass__nominal");
    // create clones, subtract ttbar from data
    TH2D *hDataF = (TH2D*)hDF->Clone("Data-bkg CR_fail");
    TH2D *hDataL = (TH2D*)hDL->Clone("Data-bkg CR_loose");
    TH2D *hDataP = (TH2D*)hDP->Clone("Data-bkg CR_pass");
    hDataF->Add(hTTF,-1.);
    hDataL->Add(hTTL,-1.);
    hDataP->Add(hTTP,-1.);
    // create the histos to hold the RPFs (data)
    TH2D *dRLF = (TH2D*)hDataL->Clone("Data R_{L/F}"); // will be divided by Fail
    TH2D *dRPL = (TH2D*)hDataP->Clone("Data R_{P/L}");	// will be divided by Loose
    TH2D *dRPF = (TH2D*)hDataP->Clone("Data R_{P/F}"); // will be divided by Fail
    // create the histos to hold the RPFs (MC)
    TH2D *ttRLF = (TH2D*)hTTL->Clone("t#bar{t} R_{L/F}"); // will be divided by Fail
    TH2D *ttRPL = (TH2D*)hTTP->Clone("t#bar{t} R_{P/L}"); // will be divided by Loose
    TH2D *ttRPF = (TH2D*)hTTP->Clone("t#bar{t} R_{P/F}"); // will be divided by Fail
    // divide everything
    dRLF->Divide(hDataF);
    dRPL->Divide(hDataL);
    dRPF->Divide(hDataF);
    ttRLF->Divide(hDataF);
    ttRPL->Divide(hDataL);
    ttRPF->Divide(hDataF);
    // go through the rpf histos and smooth out the fluctuations 
    TH2D *LFsmooth = (TH2D*)dRLF->Clone("Data R_{L/F} smooth");
    TH2D *PLsmooth = (TH2D*)dRPL->Clone("Data R_{P/L} smooth");
    double contentLF = 0;
    double contentPL = 0;
    for (auto x=0; x<LFsmooth->GetNbinsX(); x++) {
	for (auto y=0; y<LFsmooth->GetNbinsY(); y++) {
	    contentLF = LFsmooth->GetBinContent(x,y);
	    if (contentLF > 1.0) { std::cout << contentLF << "\n"; LFsmooth->SetBinContent(x,y,0.0); }
	    contentPL = PLsmooth->GetBinContent(x,y);
	    if (contentPL > 1.0) { std::cout << contentPL << "\n"; PLsmooth->SetBinContent(x,y,0.0); }
	}
    }
    LFsmooth->SetBinContent(12,2,0.0);
    LFsmooth->SetBinContent(18,2,0.0);
    PLsmooth->SetBinContent(35,19,0.0);
    // save
    TFile *fOut = TFile::Open("rootfiles/RPF_data.root","RECREATE");
    hDataF->Write();
    hDataL->Write();
    hDataP->Write();
    dRLF->Write();
    dRPL->Write();
    dRPF->Write();
    ttRLF->Write();
    ttRPL->Write();
    ttRPF->Write();
    LFsmooth->Write();
    PLsmooth->Write();
    fOut->Close();
    // make plots
    /*
    auto c = new TCanvas("c","c",800,500);
    std::cout << "check1\n";
    c->Print("plots/check_RPF.pdf[");
    c->Clear();
    std::cout << "check2\n";
    drawHists(hDataF,c);
    drawHists(hDataL,c);
    drawHists(hDataP,c);
    drawHists(dRLF,c);
    drawHists(dRPL,c);
    drawHists(dRPF,c);
    drawHists(ttRLF,c);
    drawHists(ttRPL,c);
    drawHists(ttRPF,c);
    drawHists(LFsmooth,c);
    drawHists(PLsmooth,c);
    c->Print("plots/check_RPF.pdf]");
    */
}

