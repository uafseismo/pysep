#=============================================================
# run_getwaveform.py
# 
# This script will fetch seismic waveforms, then process them, then write sac files.
# Used heavily within the UAF seismology group.
#
# This script contains a large number of examples in two categories:
# A. examples that target a current or previous bug
# B. examples of important events for modeling efforts that others may want to reproduce
#
# In the future, we will try to automatically run these examples for each code update.
# For now, we will simply try to regularly re-run the examples.
#
# contributors: Celso Alvizuri, Lion Krischer, Vipul Silwal, Carl Tape
# 
# To run this script:
# python run_getwaveform.py
#
# TO DO
# + filetags for the case iFilter = True (like lp10, bp10_40, etc)
# + provide better options and handling for data gaps (like: "toss waveform if gaps ar 0.01*length")
# + the KEVNM header cannot store the time to the 3rd millisecond character
#   probably the best approach is to write the spill-over character into another field
#   (or reconstruct the EID from the origin time, if that is your convention)
#
#================================================================

import obspy
import copy
import util_helpers
import shutil   # only used for deleting data directory
import os
import sys
from getwaveform_new import *

# EXAMPLES (choose one)
iproject = 'run_getwaveform_input'   # this is the name of file containing event info (See run_getwaveform_input.py for example)
iex = 100                            # example number within iproject.py script
                                     # iex = 215 (for looping over multiple events)

print("Running example iex =", iex)

#================================================================
# username and password for accessing embargoed data from IRIS
# Register here: http://ds.iris.edu/ds/nodes/dmc/forms/restricted-data-registration/

# Run example iex = 4 to check
user = ''
password = ''

#================================================================
# Get event info
# see getwaveform_new.py
ev_info = getwaveform()              # create event object (contains default extraction parameters)
iproject = __import__(iproject)      # file containing all the examples
ev_info = iproject.get_ev_info(ev_info, iex)   # update default extraction parameters with inputted event extarction parameters

# For looping over events
# create list if ev_info is a getwaveform object
if type(ev_info ) == getwaveform:
    ev_info_list = [ev_info]
else:
    ev_info_list  = ev_info

#================================================================
# fetch and process waveforms
# IRIS

for ii in range(0,len(ev_info_list)):
    ev_info = ev_info_list[ii]
    if ev_info.idb == 1:
        # import functions to access waveforms
        from obspy.clients.fdsn import Client
        from obspy.core.event import Event, Origin, Magnitude
        if not user and not password:
            client = Client("IRIS")
        else:
            client = Client("IRIS",user=user,password=password)
            # will only work for events in the 'IRIS' catalog
            # (future: for Alaska events, read the AEC catalog)

        # get event object
        ev = ev_info.get_event_object(c=client)
        ref_time_place = ev.copy()
        # use a different reference time and place for station subsetting
        if ev_info.rlat is not None:
            ref_time_place = ev_info.reference_time_place(ev)
        
# LLNL
    if ev_info.idb == 3:
        import llnl_db_client
        client = llnl_db_client.LLNLDBClient(
            "/store/raw/LLNL/UCRL-MI-222502/westernus.wfdisc")

        # get event time and event ID
        cat = client.get_catalog()
        mintime_str = "time > %s" % (ev_info.otime - ev_info.sec_before_after_event)
        maxtime_str = "time < %s" % (ev_info.otime + ev_info.sec_before_after_event)
        print(mintime_str + "\n" + maxtime_str)
        # ev = cat.filter(mintime_str, maxtime_str)[0]
        ev = cat.filter(mintime_str, maxtime_str)
        
        if len(ev) > 0:
            ev = ev[0]
            # Nothing happens here.  We can change later
            ref_time_place = ev
            print(len(ev))
        else:
            print("No events in the catalog for the given time period. Stop.")
            sys.exit(0)

    # Delete existing data directory
    eid = util_helpers.otime2eid(ev.origins[0].time)
    ddir = './'+ eid
    if ev_info.overwrite_ddir and os.path.exists(ddir):
        print("WARNING. %s already exists. Deleting ..." % ddir)
        shutil.rmtree(ddir)

    # track git commit
    os.system('git log | head -12 > ./' + eid + '_last_2git_commits.txt')

    # Extract waveforms, IRIS
    ev_info.run_get_waveform(c = client, event = ev, ref_time_place = ref_time_place)
