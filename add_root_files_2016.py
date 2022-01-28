#!/bin/env python
import logging
# Create logger
log = logging.getLogger("Merger")
# New: added by Brenda FE
log.setLevel(logging.DEBUG)
# New: create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# New: create formatter
formatter = logging.Formatter('%(levelname)s - %(name)s (%(asctime)s): %(message)s','%H:%M:%S')
# New: add formater to ch
ch.setFormatter(formatter)
# New: add ch to logger
log.addHandler(ch)


import optparse
import os
import multiprocessing
import re,sys,time,shutil,glob,subprocess
from random import randint
from datetime import datetime
import re
os.nice(10)

# main function is called at the end.
#
def main():
    date_time = datetime.now()
    usage = '%prog [options]'
    parser = optparse.OptionParser( usage = usage )
    parser.add_option( '-i','--inputFolder' , metavar = 'FOLDER', default=None,
                       help = 'Merge all subfolders in these folders, which can be a comma-separated list.[default: %default]' )
    parser.add_option( '--debug', metavar = 'LEVEL', default = 'INFO',
                       help= 'Set the debug level. Allowed values: ERROR, WARNING, INFO, DEBUG. [default = %default]' )
    parser.add_option( '-o','--output', metavar= "OUTFOLDER", default="output%s_%s_%s_%s_%s"%(date_time.year,
                                                                        date_time.month,
                                                                        date_time.day,
                                                                        date_time.hour,
                                                                        date_time.minute),
                         help= 'Set the output dir [default = %default]' )
    parser.add_option( '-f', '--force',action = 'store_true', default = False,
                             help = 'If this option is specifed, all root files will be remerged. [default = %default]' )
    parser.add_option( '-c', '--clean',action = 'store_true', default = False,
                             help = 'If this option is specifed, the folders will be cleand up. [default = %default]' )
    parser.add_option( '-k', '--keep',metavar= 'keep', default = "METParked",
                             help = 'Folders with this name will be kept  [default = %default]' )
    parser.add_option( '--veto',metavar= 'veto', default = None,
                             help = 'Veto a specific sample e.g. Tau_Run20  [default = %default]' )

    # Extra options. 2016 UL preVFP (APV) or postVFP (NonAPV) tag added to filename
    parser.add_option( '-a', '--apv',action = 'store_true', default = False,
                             help = 'If this option is specifed, the "preVFP" tag will be added to files. [default = %default]' )
    parser.add_option( '-n', '--nonapv',action = 'store_true', default = False,
                             help = 'If this option is specifed, the "postVFP" tag will be added to files. [default = %default]' )
    ( options, args ) = parser.parse_args()

    #format = '%(levelname)s %(name)s (%(asctime)s): %(message)s'
    #date = '%H:%M:%S'
    #logging.basicConfig( level = logging._levelNames[ options.debug ], format = format, datefmt = date )
    
    if (options.inputFolder==None and not os.path.exists("submitted_samples.txt")):
        log.error( "You must give either a input file or keep the submitted_samples.txt" )
        sys.exit(3)
    if (options.inputFolder==None and os.path.exists("submitted_samples.txt")):
        f=open("submitted_samples.txt","r")
        for line in f:
            if "outFolder:" in line:
                options.inputFolder=line.replace("outFolder:","").strip()
                break
    
    #options.output=os.path.join("/uscms/home/bfabelae/nobackup/CMSSW_10_1_9/src/NanoAOD_Submission_052019/Outputs/",options.output)
    log.info("Output directory: %s" % str(options.output))

    megeRootFiles(options)

    final_merge(options)

    removetmpfiles(options)

    if options.clean:
        cleanUp(options)

def final_merge(options):
    files=glob.glob(options.output+"/tmp/*.root")
    short_names=set()
    match1 = re.compile('(_ext)|(_Tune)|([_-][vV][123])|(_RunII)|(_13TeV)')
    
    for file in files:
        if(os.path.isdir(file)):
            continue
        file=os.path.basename(file)
        file=file.replace("crab_","")
        if "Run20" in file:
            continue
        m1=match1.search(file)
        if m1 is not None:
            shortname=file[0:m1.span()[0]]
            short_names.add(shortname)
        else:
            short_names.add(file.replace(".root",""))
    outdir=options.output
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    args=[]
    
    log.info("Final output merge:")    
    mergingdata = False
    for f in short_names:
        # check for APV tag flags and add tag.
        if (options.apv and options.nonapv):
            log.error('Must choose either the -a OR -n option')
            sys.exit(3) 
        if options.apv == True:
            outputname=os.path.join(outdir,f+"_preVFP"+".root")
        elif options.nonapv == True:
            outputname=os.path.join(outdir,f+"_postVFP"+".root")   
        else:
            outputname=os.path.join(outdir,f+".root")       
        samplelist=glob.glob(outdir+"/tmp/*%s*.root"%f)
        samplelist=filter(lambda x: (f+"0" not in x) and (f+"_HT" not in x),samplelist)
        samplelist=filter(lambda x: ("/"+f in x),samplelist)
        #samplelist=filter(lambda x: (f+"_" in x),samplelist)
        samplelist=filter(lambda x: (f+"_" in os.path.basename(x)[:len(f)+1]),samplelist)
        if len(samplelist)==1 and samplelist[0]==outputname:
            continue
        if("allData" in f):
        	mergingdata = True
        args.append([outputname, f, samplelist, options])

    if len(args)>0:
        #now merge all samples
        pool = multiprocessing.Pool(10)
        if mergingdata == False:
        	pool.map_async(hadd, args)
        else: 
        	print("\tMoving %s/tmp/allData.root to %s/allData.root" % (str(options.output), str(options.output)))
        while True:
            time.sleep(5)
            if not pool._cache: break
    if os.path.exists(options.output+"/tmp/allData.root"):
        shutil.move(options.output+"/tmp/allData.root",options.output+"/allData.root")
    

def megeRootFiles(options):
    replaceItems=[]
    listOfSamples=[]

    outputFolder=options.output+"/tmp"
    if not os.path.exists(outputFolder):
        os.makedirs(outputFolder)
    for sample in glob.glob(options.inputFolder+"/*"):
        if options.veto is not None:
            if options.veto in sample:
                continue
        if "output" in sample:
            continue
        samplelist=glob.glob(sample+"/*.root")
        for s in range(len(samplelist)):
            #samplelist[s]=samplelist[s].replace("/eos/uscms//","root://cmseos.fnal.gov//")
            samplelist[s]=samplelist[s].replace("/eos/uscms/","root://cmseos.fnal.gov//")
        #if os.path.isfile(sample):
            #continue
        csample=sample.split("/")[-1]
        print csample
        listOfSamples.append([os.path.join(outputFolder,csample+".root"),sample,samplelist,options])

    log.info("Now merging files:")
    if len(listOfSamples)>0:
        #now merge all samples
        pool = multiprocessing.Pool(10)
        pool.map_async(hadd, listOfSamples)
        while True:
            time.sleep(5)
            if not pool._cache: break
    hasData=False
    dataSamples=[]
    for data in glob.glob(outputFolder+"/"+"*.root"):
        #if "data" in data:
        if "Run20" in data:
            hasData=True
            data=data.replace(".root","")
            if data not in dataSamples:
                dataSamples.append(data)
    for dataSample in dataSamples:
        shutil.move(outputFolder+"/"+"%s.root"%(os.path.basename(dataSample)),outputFolder+"/"+"Data_%s.root"%(os.path.basename(dataSample)))
    if hasData:
        all_merged_data_files=[outputFolder+"/"+"Data_%s.root "%(os.path.basename(dataSample))  for dataSample in dataSamples]
        command= "hadd -fk -O "+outputFolder+"/"+"allData.root "+" ".join(all_merged_data_files)
        print(command)
        p = subprocess.Popen(command,shell=True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        out, err = p.communicate()
        if ("Zomie" in out) or ("Error" in out):
            
            print("-------------Problem in Data ---------------------")
            print(command)
            log.debug(out)
            log.err(err)
            print("------------------------------------")
            #log.debug(out)  
    log.info("Done.")


#method to add the Files at the end
def hadd(item):
    out, err="",""
    #item=os.path.join(outputFolder,csample+".root"),sample,samplelist,options
    outputname, sample, samplelist, options =item
    overwrite=options.force
    #print samplelist
    #print "\n"
    if (not os.path.exists(outputname)) or overwrite:
        if len(samplelist)==1:
            calling= "xrdcp "+samplelist[0]+" "+outputname
            #if "root:" in samplelist[0]:
            #    calling= "xrdcp "+samplelist[0]+" "+outputname
            #else:
            #    calling= "mv "+samplelist[0]+" "+outputname
        elif len(samplelist)==0:
            calling='echo "Error no File for %s"'%(sample)
        else:
            calling="hadd -fk -O "+outputname+" "+" ".join(samplelist)
        #print(calling)
        p = subprocess.Popen(calling,shell=True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT )
        out, err = p.communicate()
        if ("Zomie" in out) or ("Error" in out):
            
            print("-------------Problem in-----------------------")
            print(calling)
            log.debug(out)
            log.error(err)
            print("------------------------------------")
            #log.debug(out)
        #log.debug(out)
        #log.debug(err)
        print("%s is finished!"%(outputname))
    return [out, err]

def removetmpfiles(options):
    tmpFolder = options.output+"/tmp/"
    for file in glob.glob(options.output+"/tmp/*.root"):
        os.remove(file)

    log.info("Temporary files at %s have been removed." % tmpFolder)



def cleanUp(options):
    log.info('Will delete all input files!!!')
    shutil.rmtree(options.outputFolder.replace("root://cmseos.fnal.gov/","/eos/uscms/"))


if __name__ == "__main__":
    main()
