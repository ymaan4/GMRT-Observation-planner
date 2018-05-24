#!/usr/bin/env python
# plan_uGMRT_obs.py
# -*- coding: utf-8 -*-
""" Produce a command file and a text-plan for uGMRT observations."""

import sys
from sys import argv
from os.path import exists
import optparse


__author__  = "Yogesh Maan"
__license__ = "GNU GPL"
__version__ = "1.0.1"

#### function to write a block of commands ####
def write_block(src,stype,pcode,time,ofile):   # time in minutes
   '''\tWrites a block of commands to be used with GWB.'''
   ofile.write("gts'%s'\n" %src)
   ofile.write("sndsacsrc(1,12h)\n")
   ofile.write("sndsacsrc(1,12h)\n")
   ofile.write("stabct\n")
   ofile.write("/(gotosrc 15m 4)\n\n")
   if (time%10)==0:
      atime = 10
      ntime = time/10
   elif (time%5)==0:
      atime = 5
      ntime = time/5
   else:
      atime = time
      ntime = 1

   if stype=='phase' :
      ofile.write("strtndas\n")
      ofile.write("time 5s\n")
      ofile.write("/(phase_gwb.pl -t 40 -r C05 -p %s)\n" %pcode)
      ofile.write("stpndas\n")
      ofile.write("time 5s\n\n")
      ofile.write("strtndas\n")
      ofile.write("time 60s\n")
      ofile.write("stpndas\n\n\n")
   elif stype=='int' or stype=='intp':
      ofile.write("strtndas\n")
      ofile.write("time 5s\n")
      ofile.write("time %sm\n" %atime)
      for i in range(0,ntime-1):
         ofile.write("subhnd\n")
         ofile.write("time %sm\n" %atime)
      ofile.write("stpndas\n")
      ofile.write("time 5s\n\n\n")
   elif stype=='psr' :
      ofile.write("strtndas\n")
      ofile.write("time 5s\n")
      ofile.write("/(gwbpsr.start data3 %s)\n" %src)
      ofile.write("time %sm\n" %atime)
      for i in range(0,ntime-1):
         ofile.write("subhnd\n")
         ofile.write("time %sm\n" %atime)
      ofile.write("stpndas\n")
      ofile.write("/(gwbpsr.stop)\n")
      ofile.write("time 5s\n\n\n")
   else:
      ofile.truncate()
      print "ERROR: Specify correct source type phase/int/psr."
      print "Halting !!"




def main():
   """ Produce a command file, src-list and a text-plan for uGMRT observations."""

   ### parse command-line arguments...
   parser = optparse.OptionParser(version='%prog version 1.0.1')
   parser.add_option('-l', '--loop', help='The file-name that contains information of all the sources to be observed in a loop.',dest="infile",action='store')
   parser.add_option('-p', '--pcode', help='The GMRT proposal project-code (e.g. 33_001 )',dest='pcode',action='store')
   parser.add_option('-c', '--flux-cal', help='The flux-calibrator to be used (e.g. 3C48 )',dest='cal',action='store')
   (opts, args) = parser.parse_args(sys.argv)
   if opts.infile is None or opts.pcode is None or opts.cal is None:
       print "Some mandatory argument(s) missing !!\n"
       parser.print_help()
       exit(-1)

   print "\n"

   ### Check different files ############################################
   cmdfile = "obs.txt"
   planfile = "ugmrt_obs.plan"
   if exists(cmdfile) or exists(planfile):
      print "File 'obs.txt' and/or 'ugmrt_obs.plan' already exists in current folder, (re)move these/it and re-execute !!"
      exit(0)
   inp = open(opts.infile, 'r')
   out = open(cmdfile, 'w')


   #### First Write the command-file ##################################
   ## ---- preamble ----
   preamble = """cmode 1\nlnkndas\n\nsubar 4\ndellist 2\ndellist 2\n
addlist '/odisk/gtac/cmd/%s/src.list'\n
goout\ngosacout\n\n*goin\n*gosacin\n
/(gwbpsr.init)\n\n\n\n$1\n """ %opts.pcode
   out.write(preamble)
   out.write("\n")
   ## --- now blocks for each source ------
   line = inp.readline()
   ns = 1
   intmode=False
   while line:
       src,stype,stime = line.split()
       time = int(stime)
       if stype=="phase":
          pcal=src
       if stype=="int" or stype=="intp":
          intmode=True
       if stype=="intp":
          intpcal=src
       write_block(src,stype,opts.pcode,time,out)
       line = inp.readline()
       ns += 1
   ## -- now the end part
   out.write("\ngoto 1\n\n")
   out.write("/(gwbpsr.finish)\n\n")
   out.write("/bell\n")
   out.write("/bell\n\n")
   out.write("end\n")
   print "Command-file 'obs.txt' written-out for %d sources in each loop." %ns
   ##----------------------------------
   inp.close()
   out.close()
   ###############################################################
   ### Plan file #################################################

   inp = open(opts.infile, 'r')
   plan = open(planfile, 'w')
   dashline="-----------------------------------------------------------------------"
   thickline="========================================================================="
   plan.write("\n%s\n" %dashline)
   plan.write("1. Settings as per the accompanying setup file\n%s\n" %dashline)
   plan.write("2. %s           Power equalize to 150 cnts. GAINEQ: ON\n" %opts.cal)
   block="""   Check fringes - matmon
   Check bandshapes and deflection - dasmon
   Check RFI in antennas
   Check antenna with power and phase jump history
   Make antenna selection"""
   plan.write("%s\n%s\n" %(block,dashline))
   plan.write("3. Configure GAC, GWB for PA\n\n")
   block="""   (All central square antennas and first arm antennas)
                        C00 C01 C02 C03 C04 C05 C06
                        C08 C09 C10 C11 C12 C13 C14
                        W01 W02
                        E02 E03
                        S01 S02"""
   plan.write("%s\n" %block)
   plan.write("   Total antennas = 20\n")
   plan.write("%s\n" %dashline)
   plan.write("%s\n" %thickline)
   plan.write("4. OBSERVE/RECORD-DATA\n\n")
   sp="   "
   plan.write("%s%s\n" %(sp,dashline))
   if(intmode):
       plan.write("%s4(0). Observe flux-cal %s ONLY IN INTERFEROMETRIC MODE for 6 to 8 minutes\n\n" %(sp,opts.cal))
   plan.write("%s%s\n" %(sp,dashline))
   plan.write("%s4(A). DO PHASING ON %s \n\n" %(sp,pcal))
   block="""        Using Antennas whichever of the following available :
        (All central square antennas and first arm antennas)
                        C00 C01 C02 C03 C04 C05 C06
                        C08 C09 C10 C11 C12 C13 C14
                        W01 W02
                        E02 E03
                        S01 S02
        If any particular antenaa/dish shows high levels of RFI, please exclude
        it from phasing, GAC and GWB."""
   plan.write("%s\n\n" %block)
   plan.write("%s%s\n" %(sp,dashline))
   plan.write("%s4.(B) Start the command file \"obs.txt\" in LOOP.\n" %sp)
   plan.write("        (Several loops;  see 4(C) for when to stop)\n\n")
   plan.write("      EACH LOOP HAS:\n\n")
   spp="                "
   line = inp.readline()
   ns = 1
   while line:
       src,stype,stime = line.split()
       time = int(stime)
       if stype=="phase":
          plan.write("%s%d.      %s     (re-)phasing and record 1 min\n" %(spp,ns,src))
       else:
          plan.write("%s%d.      %s     %d MINUTES\n" %(spp,ns,src,time))
       line = inp.readline()
       ns += 1
   plan.write("\n\n")
   plan.write("%s%s\n" %(sp,dashline))
   plan.write("%s4.(C) About 10-12 minutes before the end of observations, stop the\n" %sp)
   plan.write("         above loop and observe:\n\n")
   if(intmode):
      plan.write("           1. phase-cal %s ONLY IN INTERFEROMETRIC MODE for 5 minutes.\n" %intpcal)
      plan.write("           2. flux-cal %s ONLY IN INTERFEROMETRIC MODE for 6 to 8 minutes.\n" %opts.cal)
   else:
      plan.write("           1. flux-cal %s ONLY IN INTERFEROMETRIC MODE for 6 to 8 minutes.\n" %opts.cal)

   plan.write("%s\n\n\n" %thickline)
   plan.write("5. End of observations and Close the pulsar chain using cmd \"/(gwbpsr.finish)\" in user4 window.\n\n")
   plan.write("%s\n" %dashline)
   inp.close()
   plan.close()
   print "Plan-file 'ugmrt_obs.plan' written-out for %d sources in each loop." %ns
   print "\n"
   ###############################################################




if __name__ == "__main__":
    main()



