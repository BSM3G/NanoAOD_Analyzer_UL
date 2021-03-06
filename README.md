## NanoAOD UL Analyzer documentation

**This version of The Analyzer is adapted for use with NanoAODv8 Ultra Legacy samples. This documentation outlines important changes in usage from the original version. To successfully run the UL version, it is highly recommended to become familiar with the documentation of the original Analyzer, which can be found at:**
### [https://github.com/VandyHEP/NanoAOD_Analyzer/wiki](https://github.com/VandyHEP/NanoAOD_Analyzer/wiki)

**All the information you need about the framework, installation and usage is there. Don't forget to check it out.**

## General Notes
- CMSSW_10_6_29 is recommended for analyses using UL NanoAODv8 
- If using with the NanoAOD_submission framework, change cloned directory name to NanoAOD_Analyzer, or export ANALYSISDIR = <path>/NanoAOD_Analyzer_UL .

## Configuration Files
### Run_info.in
- New pileup histogram names for UL are:
  - MC
     - 2016 preVFP: mc2016preVFP_pileup_20UL16.root, postVFP: mc2016postVFP_pileup_20UL16.root
     - 2017: mc2017_pileup_20UL17.root
     - 2018: mc2018_pileup_20UL18.root
  - Data
     - 2016 preVFP: PileUpReweighting2016ULpreVFP.root, postVFP: PileUpReweighting2016ULpostVFP.root
     - 2017: PileUpReweighting2017UL.root
     - 2018: PileUpReweighting2018UL.root
- βis2016preVFPβ Boolean flag must be included. (True if running 2016preVFP MC or data).
- 2017 no longer requires special PU calculations, this part in the config file can be removed. 

### Jet_info.in
- "Tight" ID now recommended for jets of all years
- EE noise corrections no longer required for 2017 data.
- New DeepCSV working point discriminant cuts.
  - βMediumβ WP ->      ππππ: 0.6001(πππππΉπ),  0.5847(πππ π‘ππΉπ)         ππππ:0.4506           ππππ:0.4168 


## Notes on Merging 2016 Pre/Post VFP Runs
- Resulting MC ROOT files from pre/post VFP 2016 runs should not be merged with hadd before running through the Plotter because they are not normalized to appropriate proportion of luminosity. 
- Data ROOT files can be merged with hadd.


