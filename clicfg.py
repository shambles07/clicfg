#!/usr/bin/env python
##############################################################################################################
# Title   : clicfg.py
# Author  : Rob Ladendorf
# Usage   : Generate call files for use with Asterisk
##############################################################################################################
# Creates call files and offers the user the ability to set each option explicitly via cli arguments.
# Currently, the script is only configured to handle calls to extension/context, so extension/context/priority _must_ be defined.
#
# TODO:     Add specific handling for application/data (for simple call files that send to an application with set options)
#           I would also like to perhaps include more functions in the code, and also accept multiple Setvar options.
#
#           The call files are also only written to a local directory--perhaps another script can be used for setting the proper file ownership?
#           This could actually be accomplished by calling stat on /var/spool/asterisk.
#
# NOTE:     This script does not currently handle error logging properly, i.e. it does not handle error logging at all.
#           The only logging offered is for debug and info logs. So perhaps we can remove some of the verbosity handling.
#

from datetime import datetime
from jinja2 import Template
import argparse
from os import path, chmod, chown, mkdir
from uuid import uuid4
import logging
import sys

# set the current directory
pwd = path.abspath(path.curdir)
# set the output directory
callfile_dir = path.join(pwd, 'callfiles')
# get the current date/time
now = datetime.now()
# formatting the date
date = datetime.strftime(now, "%Y%m%d_%H%M%S")
# get a random uuid for call file output and set the callfile name
random = int(str(uuid4()).split('-')[-3], 16)
callfile = path.join(callfile_dir, "%s_%s.call" % (date, random))

# configure argument parser
argparse = argparse.ArgumentParser(description="Callfile Generator written in Python")

# add necessary arguments
argparse.add_argument('-ch', '--channel', help="Channel for call file", type=str, required=True)
argparse.add_argument('-c', '--context', help="Context to use for the call", type=str, required=True)
argparse.add_argument('-e', '--exten', help="Extension to use for the call", type=int, required=True)
argparse.add_argument('-p', '--priority', help="Priority to use for the call", type=int)
argparse.add_argument('-cnum', '--cid-number', help="Caller ID for call file", type=int)
argparse.add_argument('-cname', '--cid-name', help="Caller ID name for call file", type=str)
argparse.add_argument('-w', '--wait-time', help="Wait time for call file", type=int)
argparse.add_argument('-m', '--max-retries', help="The maximum number of retries", type=int)
argparse.add_argument('-r', '--retry-time', help="Time to wait inbetween retries", type=int)
argparse.add_argument('-a', '--account', help="Account code for the call", type=str)
argparse.add_argument('-s', '--setvar', help="Variable to set for the call", type=str)
argparse.add_argument('-v', '--verbose', help="Set verbosity of the program, the more -v the merrier", action="count", default=0)
argparse.add_argument('-d', '--dry-run', help="Dry run of the script", action="store_true")

# parse arguments
args = argparse.parse_args()

# set logging level based on verbosity flag count
if args.__getattribute__("verbose"):
    if args.verbose == 1:
        level = logging.CRITICAL
    elif args.verbose == 2:
        level = logging.WARNING
    elif args.verbose == 3:
        level = logging.INFO
    elif args.verbose >= 4:
        level = logging.DEBUG
    else:
        level = logging.ERROR
else:
    level = logging.INFO

# configure logging, log to file set to append
logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    # filename="clicfg.log",
    # filemode="a",
    level=level
)

logging.info("Script started executing!")

# this section reads the arguments provided and parses them into keyword arguments.
# the alternative to this method would be using if statements for each keyword in the template.

# init kwargs dict
kwargs = {}
# iterate over parsed arguments, if option is not set, ignore, else add to kwargs
for item in args._get_kwargs():
    if item[1] != None:        
            kwargs[item[0]] = item[1]
            logging.debug("{} has been set as {}".format(item[0], item[1]))

# build the caller id string using both cid number and cid name
# accepts either both options or just cid number. hence the strange nested try blocks
if kwargs.has_key("cid_name") and kwargs.has_key("cid_number"):
    kwargs["callerid"] = "\"{}\" <{}>".format(kwargs["cid_name"], kwargs["cid_number"])
    logging.debug("Received both cid name and cidnum")
elif kwargs.has_key("cid_number") and not kwargs.has_key("cid_name"):
    logging.debug("Only cid number received")
    kwargs["callerid"] = "<{}>".format(kwargs["cid_number"])
elif kwargs.has_key("cid_name") and not kwargs.has_key("cid_number"):
    logging.debug("Only cid name received, setting cid number value to exten value")
    kwargs["callerid"] = "\"{}\" <{}>".format(kwargs["cid_name"], kwargs["exten"])
elif not kwargs.has_key("cid_name") and not kwargs.has_key("cid_number"):
    logging.debug("No CID specified")
else:
    logging.error("Unable to set callerid due to some strange error")

# read the template text into a variable
template = open('template.j2', 'r').read()
# get the full path of the output callfile
callfile = path.join(callfile_dir, callfile)
# parse the template file using the arguments provided
output = Template(template).render(**kwargs).split('\n')
# remove non-empty lines from the file
non_empty = [line for line in output if line.strip() != ""]

# check if dry-run is set, if so print to console
if args.__getattribute__("dry_run"):
    logging.info("Dry run option set, printing to console then exiting")
    print("Dry run of the call file generator, printing to console:")
    print("\n".join(non_empty))
    logging.info("Exiting due to dry-run option")
    sys.exit(1)

if not path.isdir(callfile_dir):
    logging.debug("Callfile directory {} does not exist, creating it".format(callfile_dir))
    mkdir(callfile_dir)

# here is where the file should be written to.
with open(callfile, 'w') as cfh:
    logging.debug("Writing call file {} to directory {}".format(callfile, callfile_dir))
    cfh.write("\n".join(non_empty))
    cfh.close()

print("Success! File written to: {}".format(callfile))

logging.info("Script is now exiting!")
