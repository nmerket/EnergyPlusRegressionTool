#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import shutil
import subprocess
from Structures import *
from multiprocessing import current_process
import glob


path = os.path.dirname(__file__)
script_dir = os.path.abspath(path)

def execute_energyplus(base_dir, entry_name, case_dir, executable_name, run_type, min_reporting_freq, parametric_file, weather_file_name, eplus_install):
    
    # setup a few paths
    builddir = base_dir
    simdir = case_dir
    energyplus = os.path.join(builddir, executable_name)
    idd = os.path.join(builddir, 'Energy+.idd')

    # external tools also
    basement      = os.path.join(eplus_install, 'PreProcess', 'GrndTempCalc', 'Basement')
    slab          = os.path.join(eplus_install, 'PreProcess', 'GrndTempCalc', 'Slab')
    basementidd   = os.path.join(eplus_install, 'PreProcess', 'GrndTempCalc', 'BasementGHT.idd')
    slabidd       = os.path.join(eplus_install, 'PreProcess', 'GrndTempCalc', 'SlabGHT.idd')
    expandobjects = os.path.join(eplus_install, 'ExpandObjects')
    epmacro       = os.path.join(eplus_install, 'EPMacro')
    readvars      = os.path.join(eplus_install, 'PostProcess', 'ReadVarsESO')
    parametric    = os.path.join(eplus_install, 'PreProcess', 'ParametricPreProcessor', 'parametricpreprocessor')
    
    # Save the current path so we can go back here
    start_path = os.getcwd()

    try:
        
        # Copy the weather file into the simulation directory
        if run_type != ForceRunType.DD:
            shutil.copy(weather_file_name, os.path.join(simdir, 'in.epw'))

        # Copy the idd into the simulation directory
        shutil.copy(idd, simdir)

        # Switch to the simulation directory
        os.chdir(simdir)

        # Run EPMacro as necessary
        if os.path.exists('in.imf'):
            print("IMF file exists")
            lines = []
            with open('in.imf') as f:
                lines = f.readlines()
            newlines = []
            for line in lines:
                if '##fileprefix' in line:
                    newlines.append('')
                    print ("Replaced fileprefix line with a blank")
                else:
                    newlines.append(line)
            with open('in.imf', 'w') as f:
                for line in newlines:
                    f.write(line)
            macro_run = subprocess.Popen(epmacro, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            macro_run.communicate()
            os.rename('out.idf','in.idf')
            
        # Run Preprocessor -- after EPMacro?
        if parametric_file:
            parametric_run = subprocess.Popen([parametric, 'in.idf'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            parametric_run.communicate()
            candidate_files = glob.glob('in-*.idf')
            if len(candidate_files) > 0:
                sorted_candidates = sorted(candidate_files)
                file_to_run_here = sorted(candidate_files)[0]
                if os.path.exists('in.idf'):
                    os.remove('in.idf')
                os.rename(file_to_run_here, 'in.idf')
            else:
                #print("in-000001.idf file doesn't exist -- parametric preprocessor failed")
                return [base_dir, entry_name, False, current_process().name]
                
        # Run ExpandObjects and process as necessary
        expand_objects_run = subprocess.Popen(expandobjects, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        expand_objects_run.communicate()
        if os.path.exists('expanded.idf'):
            if os.path.exists('in.idf'):
                os.remove('in.idf')
            os.rename('expanded.idf', 'in.idf')

            if os.path.exists('BasementGHTIn.idf'):
                shutil.copy(basementidd, simdir)
                basement_run = subprocess.Popen(basement, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                basement_run.communicate()
                appendText = ''
                with open('EPObjects.TXT') as f:
                    appendText = f.read()
                with open('in.idf', 'a') as f:
                    f.write("\n%s\n" % appendText)
                os.remove('RunINPUT.TXT')
                os.remove('RunDEBUGOUT.TXT')
                os.remove('EPObjects.TXT')
                os.remove('BasementGHTIn.idf')
                os.remove('MonthlyResults.csv')
                os.remove('BasementGHT.idd')

            if os.path.exists('GHTIn.idf'):
                shutil.copy(slabidd, simdir)
                slab_run = subprocess.Popen(slab, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                slab_run.communicate()
                appendText = ''
                with open('SLABSurfaceTemps.TXT') as f:
                    appendText = f.read()
                with open('in.idf', 'a') as f:
                    f.write("\n%s\n" % appendText)
                os.remove('SLABINP.TXT')
                os.remove('GHTIn.idf')
                os.remove('SLABSurfaceTemps.TXT')
                os.remove('SLABSplit Surface Temps.TXT')
                os.remove('SlabGHT.idd')
        
        # Set up environment
        os.environ["DISPLAYADVANCEDREPORTVARIABLES"] = "YES"
        os.environ["DISPLAYALLWARNINGS"] = "YES"
        if run_type == ForceRunType.DD:
            os.environ["DDONLY"] = "Y"
            os.environ["REVERSEDD"] = ""
            os.environ["FULLANNUALRUN"] = ""
        elif run_type == ForceRunType.ANNUAL:
            os.environ["DDONLY"] = ""
            os.environ["REVERSEDD"] = ""
            os.environ["FULLANNUALRUN"] = "Y"
        elif run_type ==  ForceRunType.REVERSEDD:
            os.environ["DDONLY"] = "Y"
            os.environ["REVERSEDD"] = "Y"
            os.environ["FULLANNUALRUN"] = ""
        elif run_type ==  ForceRunType.NONE:
            os.environ["DDONLY"] = ""
            os.environ["REVERSEDD"] = ""
            os.environ["FULLANNUALRUN"] = ""
        else:
            pass
            #nothing

        # use the user-entered minimum reporting frequency (useful for limiting to daily outputs for annual simulation, etc.)
        os.environ["MINREPORTFREQUENCY"] = min_reporting_freq.upper()

        # Execute EnergyPlus
        eplus_run = subprocess.Popen(energyplus, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        eplus_run.communicate()
        
        # Execute readvars
        csv_run = subprocess.Popen(readvars, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        csv_run.communicate()
        with open('test.mvi', 'w') as f:
            f.write("eplusout.mtr\n")
            f.write("eplusmtr.csv\n")
        mtr_run = subprocess.Popen([readvars, 'test.mvi'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        mtr_run.communicate()
        
        # Handle outputs (eplusout.csv and eplusmtr.csv) for reverse DD cases
        if run_type == ForceRunType.REVERSEDD:
            # find out how many DD's there are
            num_DDs = 0
            with open("in.idf") as f:
                for line in f:
                    if "SizingPeriod:DesignDay," in line:
                        num_DDs += 1
            
            ## read all lines from csv
            csv_contents = []
            with open("eplusout.csv") as f:
                for line in f:
                    csv_contents.append(line)
            meter_exists = os.path.exists("eplusmtr.csv")
            mtr_contents = []
            if meter_exists:
                with open("eplusmtr.csv") as f:
                    for line in f:
                        mtr_contents.append(line)
            
            # now find out how many lines of data there are in each file and each environment
            csv_data_rows = len(csv_contents) - 1
            csv_data_rows_per_envrn = csv_data_rows / num_DDs
            if meter_exists:
                mtr_data_rows = len(mtr_contents) - 1
                mtr_data_rows_per_envrn = mtr_data_rows / num_DDs
            
            # write the files back out in the appropriate order
            shutil.copy("eplusout.csv", "eplusout-before_revDD_swapback.csv")
            with open("eplusout.csv", "w") as f:
                f.write("%s" % csv_contents[0])
                for row_num in range(csv_data_rows_per_envrn+1, 2*csv_data_rows_per_envrn+1):
                    f.write("%s" % csv_contents[row_num])
                for row_num in range(1, csv_data_rows_per_envrn+1):
                    f.write("%s" % csv_contents[row_num])
                if num_DDs > 2:
                    for row_num in range(2*csv_data_rows_per_envrn+1, csv_data_rows+1):
                        f.write("%s" % csv_contents[row_num])
            if meter_exists:
                shutil.copy("eplusmtr.csv", "eplusmtr-before_revDD_swapback.csv")
                with open("eplusmtr.csv", "w") as f:
                    f.write("%s" % mtr_contents[0])
                    for row_num in range(mtr_data_rows_per_envrn+1, 2*mtr_data_rows_per_envrn+1):
                        f.write("%s" % mtr_contents[row_num])
                    for row_num in range(1, mtr_data_rows_per_envrn+1):
                        f.write("%s" % mtr_contents[row_num])
                    if num_DDs > 2:
                        for row_num in range(2*mtr_data_rows_per_envrn+1, mtr_data_rows+1):
                            f.write("%s" % mtr_contents[row_num])
                            
        os.remove('Energy+.idd')
        return [base_dir, entry_name, True, False, current_process().name]
        
    except Exception as e:
        f = open("aa_testSuite_error.txt",'w')
        print(e, file=f)
        return [base_dir, entry_name, False, False, current_process().name]
        
    finally:
        os.chdir(start_path)
        
if __name__ == "__main__":    

    build_directory    = sys.argv[1]
    sim_run_directory  = sys.argv[2]
    executable_name    = sys.argv[3]
    force_run_type     = sys.argv[4]
    parametric_file    = sys.argv[5]
    weather_file       = sys.argv[6]
    eplus_install_path = sys.argv[7] 
        
    execute_energyplus(build_directory, sim_run_directory, executable_name, force_run_type, parametric_file, weather_file, eplus_install_path)