#!/usr/bin/env python
from __future__ import print_function
import sys
import glob
import argparse
import csv
import os 
import random

# set up some things ahead of time    
path = os.path.dirname(__file__)
script_dir = os.path.abspath(path)
slash = os.sep

class csv_file_entry(object):
    
    def __init__(self, csv_row):
        self.filename = csv_row[0]
        self.weatherfilename = csv_row[1]
        self.has_weather_file = (self.weatherfilename != "")
        self.external_interface = (csv_row[2] == "Y")
        self.ground_ht = (csv_row[3] == "Y")
        self.external_dataset = (csv_row[4] == "Y")
        self.parametric = (csv_row[5] == "Y")
        self.macro = (csv_row[6] == "Y")
        self.delight = (csv_row[7] == "Y")
        self.underscore = (self.filename[0] == '_')

class filelist_argsbuilder_forgui():
    
    def __init__(self):
        
        # establish defaults
        self.all = False
        self.extinterface = False
        self.groundht = False
        self.dataset = None
        self.delight = False
        self.macro = True
        self.parametric = False
        self.random = 0
        self.weatherless = True
        self.underscore = True
        self.verify = None
        self.check = False
        self.verify = None
        self.master_data_file = "FullFileSetDetails.csv"
        
        # some special things for GUI
        self.gui = True

class file_list_builder(object):

    def __init__(self, args):
        
        # if the 'all' argument is present, turn on all the rest
        if args.all:
            args.extinterface, args.groundht, args.dataset, args.delight, args.macro, args.parametric, args.underscore, args.weatherless = [True, True, True, True, True, True, True, True]

        # initialize callbacks to None
        self.callback_func_print = None
        self.callback_func_init = None
        self.callback_func_increment = None

    def set_callbacks(self, callback_print, callback_init, callback_increment):
        self.callback_func_print = callback_print
        self.callback_func_init = callback_init
        self.callback_func_increment = callback_increment
                
    def build_verified_list(self, args):

        self.my_print("Starting to build file list")

        # initialize the status flag to True
        success = True

        # then wrap the processes inside a try block to trap for any errors
        try:
        
            # create an empty list
            self.selected_input_file_set = []

	    # for convenience, count the number of rows first, this should be a cheap operation anyway
            with open(args.master_data_file) as csvfile:
                num_lines_approx = csvfile.read().count('\n')
            self.my_init(num_lines_approx+1)
                                 
	    # get all rows of data
            with open(args.master_data_file) as csvfile:
                    reader = csv.reader(csvfile)
                    row_num = 0
                    for row in reader:
                            self.my_increment()
                            row_num += 1
                            if row_num == 1:
                                    continue
                            this_entry = csv_file_entry(row)
                            self.selected_input_file_set.append(this_entry)
            
            # then sort it by filename
            self.selected_input_file_set.sort(key=lambda x: x.filename.lower())
            self.my_increment()
            
            # initialize a list of files that weren't found
            self.input_files_eliminated = set()
            self.input_files_found_not_listed = set()
            
            # if we are verifying using input file directories,
            if args.verify != None:

                    self.my_print("Verifying idf list using directory: %s" % args.verify)
                    
                    # read in the files in the directory and remove the extensions 
                    files_in_this_dir = self.read_input_files_in_dir(args.verify)
                    files_no_extensions = [ os.path.splitext(infile)[0] for infile in files_in_this_dir ]
                    just_filenames = [ infile.split(os.sep)[-1] for infile in files_no_extensions ]

                    # check all files in the main set and see if any are missing
                    for infile in self.selected_input_file_set:
                            
                            # if it is missing add it to the files to be eliminated
                            if not infile.filename in just_filenames:

                                    # sets only include unique entities
                                    self.input_files_eliminated.add(infile)

                    # include a report of files found in the directory not represented in the file list
                    for infile in just_filenames:
                            
                            # if the file found by globbing is missing from the csv dataset
                            if infile in self.selected_input_file_set:
                                    
                                    # add it to the report
                                    self.input_files_found_not_listed.add(infile)
                                            
                    # now prune off files missing in the verification directories 
                    if len(self.input_files_eliminated) > 0:
                            for i in self.input_files_eliminated:
                                    self.selected_input_file_set.remove(i)

            self.my_print("File list build completed successfully")
            
        except:
            self.my_print("An error occurred during file list build")
            success = False
                                    
        return success, self.selected_input_file_set, self.input_files_eliminated, self.input_files_found_not_listed

    def print_file_list_to_file(self, args):
                    
        # if we aren't running in the gui, we need to go ahead and down select and write to the output file if we aren't running from the gui
        if not args.gui:
            with open(args.output_file, 'w') as outfile:
                for i in self.selected_input_file_set:
                    if i.has_weather_file:
                        print("%s %s" % (i.filename, i.weatherfilename), file=outfile)
                    else:
                        print("%s" % (i.filename), file=outfile)
        
        print("File list build complete")
        
    def read_input_files_in_dir(self, dir):
        extensions_to_match = ['*.idf', '*.imf']
        files_in_dir = []
        for extension in extensions_to_match:
            files_in_dir.extend(glob.glob(dir + os.sep + extension))
        return files_in_dir

    def down_select_idf_list(self, args):
        
        idf_list = self.selected_input_file_set
        
        # now trim off any of the specialties if the switches are false (by default)
        if not args.extinterface: # only include those without external interface dependencies
            idf_list = [ idf for idf in idf_list if not idf.external_interface ]
        if not args.groundht: # only include those without ground ht dependencies
            idf_list = [ idf for idf in idf_list if not idf.ground_ht ]
        if not args.dataset: # only include those without external dataset dependencies
            idf_list = [ idf for idf in idf_list if not idf.external_dataset ]
        if not args.parametric: # only include those without parametric preprocessor dependencies
            idf_list = [ idf for idf in idf_list if not idf.parametric ]
        if not args.weatherless: # only include those that DO have weather files
            idf_list = [ idf for idf in idf_list if idf.has_weather_file ]
        if not args.macro: # only include those without macro dependencies
            idf_list = [ idf for idf in idf_list if not idf.macro ]
        if not args.delight: # only include those without delight dependencies
            idf_list = [ idf for idf in idf_list if not idf.delight ]
        if not args.underscore: # only include those that don't start with an underscore
            idf_list = [ idf for idf in idf_list if not idf.underscore ]
        # do random down selection as necessary:
        if args.random > 0:
            if len(idf_list) <= args.random: # just take all of them
                pass
            else: # down select randomly
                indeces_to_take = sorted(random.sample(xrange(len(idf_list)), args.random))
                idf_list = [ idf_list[i] for i in indeces_to_take ]
        # return the trimmed list
        self.selected_input_file_set = idf_list
        return idf_list

    def my_init(self, num_files):
            if self.callback_func_init:
                self.callback_func_init(num_files)

    def my_increment(self):
            if self.callback_func_increment:
                self.callback_func_increment()

    def my_print(self, msg):
            if self.callback_func_print:
                    self.callback_func_print(msg)
            else:
                    print(msg)
                        
if __name__ == "__main__":
    
    # parse command line arguments 
    parser = argparse.ArgumentParser(description="""Create EnergyPlus test file inputs for a specific configuration.  Can be executed in 2 ways:
                                                  1: Arguments can be passed from the command line, such as `%s -r 3 -w' .. Most useful for scripting, or 
                                                  2: An argument class can be created using the filelist_argsbuilder_forgui class and passed into a file_list_builder instance .. Most useful for UIs""" % sys.argv[0])
    parser.add_argument('-a', '--all',          action='store_true', help='Includes all files found in the master, overrides other flags, can still down select with -r')
    parser.add_argument('-e', '--extinterface', action='store_true', help='Include external interface test files')
    parser.add_argument('-g', '--groundht',     action='store_true', help='Include ground heat transfer test files')
    parser.add_argument('-d', '--dataset',      action='store_true', help='Include external dataset test files')
    parser.add_argument('-l', '--delight',      action='store_true', help='Include DeLight test files')
    parser.add_argument('-m', '--macro',        action='store_true', help='Include files with macro definitions')
    parser.add_argument('-p', '--parametric',   action='store_true', help='Include parametric preprocessor test files')
    parser.add_argument('-r', '--random',       nargs='?', default=0, type=int, metavar='N', help='Get random selection of <N> files')
    parser.add_argument('-w', '--weatherless',  action='store_true', help='Include files that do not have a weather file')
    parser.add_argument('-u', '--underscore',   action='store_true', help='Include files that start with an underscore')
    parser.add_argument('-v', '--verify', metavar='<path>', nargs=1, help='Performs verification that files exist in a directory.  Excludes those that do not.  Argument is a path to a test file directory containing idfs and imfs.')
    args = parser.parse_args()
    
    # these were originally inputs, but that is really bulky
    # they are now hardwired and can be manipulated outside of the script if needed
    args.master_data_file = os.path.join(script_dir, "FullFileSetDetails.csv")
    args.output_file = os.path.join(script_dir, "files_to_run.txt")

    # backup the previous output file if one already exists and then delete it
    if os.path.isfile(args.output_file):
        backup_file = os.path.join(os.path.dirname(args.output_file), "backup_%s" % os.path.basename(args.output_file))
        if os.path.isfile(backup_file):
            try:
                os.remove(backup_file)
            except:
                print("An error occurred when trying to remove the previous backup output file: %s; aborting..." % backup_file)
        try:
            os.rename(args.output_file, backup_file)
        except:
            print("An error occurred when trying to backup the previous output file: %s; aborting..." % args.output_file)

    if args.verify != None:
        args.verify = args.verify[0] # argparse insists on returning a list, even if just 1
        args.check = True
    else:
        args.check = False
    
    # for running this as a script, add some dummies:
    args.gui = False
    
    # instantiate the main class to run
    this_builder = file_list_builder(args)
    
    # The following two calls will actually return values
    # In a GUI, we will capture these returns as desired to do further stuff with
    # In a script, we will just let the class instance hang on to the values and write out the list file
    
    # build a base file list verified with any directories requested
    this_builder.build_verified_list(args)
    
    # down select the idf list based on command line arguments
    this_builder.down_select_idf_list(args)
    
    # and go ahead and print to the output file
    this_builder.print_file_list_to_file(args)