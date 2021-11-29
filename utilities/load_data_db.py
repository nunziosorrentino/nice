#!/usr/bin/env python

"""

 Script name: load_data_db.py

 Description:
    Load data to database

    sample command

    python djangoigm/utilities/load_data_db.py -d -i djangoigm/data/virgo_channels.txt djangoigm/data/config_db_localhost.json

    #slwebstest3
    python $HOME/VirgoSw/djangoigm/utilities/load_data_db.py -d -i $HOME/VirgoSw/djangoigm/data/virgo_channels.txt $HOME/VirgoSw/djangoigm/data/config_db_slwebtest3.json
"""


#######################################
# Importing modules
#######################################

import os
import glob
import json
import platform
import shutil
import sys
import time
from optparse import OptionParser

import numpy as np
import pandas as pd
import django

from customlogger import CustomLogger
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

#######################################
# Additional information
#######################################
__author__ = "Massimiliano Razzano"
__copyright__ = "Copyright 2017-2020, Massimiliano Razzano"
__credits__ = ["Line for credits"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "M. Razzano"
__email__ = "massimiliano.razzano@pi.infn.it"
__status__ = "Production"

#######################################
# General variables
#######################################

os_system = platform.system()
script_name = os.path.split(sys.argv[0])[1].split('.')[0]
script_path = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]))
running_python_version = int(sys.version[0])
work_dir = os.getcwd()

#######################################
# General functions
#######################################
def read_json_file(m_filename):
    m_out_dict = json.loads(open(m_filename).read())

    #m_out_dict = {}
    #for ki in m_dict.keys():
    #    m_out_dict[str(ki)]=str(m_dict[ki])
    #return ast.literal_eval(json.loads(open(m_filename).read()))

    return m_out_dict

#######################################################
# Main
#######################################################

if __name__ == '__main__':

    usg = "\033[1;31m%prog [ options] summary_meta.txt\033[1;m \n"

    desc = "\033[34mBuild a dataset of coefficients\033[0m"

    parser = OptionParser(description=desc, usage=usg)
    parser.add_option("-d", "--debug", default=False, action="store_true", help="Debug mode")
    parser.add_option("-l", "--logging", default=False, action="store_true", help="enable file logging")
    parser.add_option("-o", "--outdir", type="string", default=None, help="Output Directory")
    parser.add_option("-i", "--input", type="string", default=None, help="Input data")
    #parser.add_option("-m", "--metadata", type="string", default=None, help="CSV Summary metadata")
    #parser.add_option("-f", "--format", type="string", default="hdf5", help="format of  dataset")
    parser.add_option("-m", "--model", type="string", default=None, help="Model name (i.e. the table)")
    parser.add_option("-c", "--channel", type="string", default=None, help="Channel name (just for glitches)")
    parser.add_option("-D", "--detector", type="string", default=None, help="Detector name")
    parser.add_option("-p", "--pipeline", type="string", default=None, help="Pipeline name")

    #parser.add_option("-N", "--noise", default=True, action="store_true", help="Add a set of noise data")
    #parser.add_option("-t", "--tmin", type="float", default=None, help="Minimum time")
    #parser.add_option("-T", "--tmax", type="float", default=None, help="Maximum time")
    #parser.add_option("-r", "--ratiosplit", type="float", default=0.7, help="Train-validation split ratio (e.g. 0.7)")
    #parser.add_option("-p", "--proc", type="string", default="spec", help="Processing (archive=just archive; spec=spectrograms)")
    #parser.add_option("-D", "--downsample", type="float", default=None, help="Downsample frequency")

    (options, args) = parser.parse_args()

    debug_mode = options.debug
    logging = options.logging
    output_dir = options.outdir
    input_filename = options.input
    model_name = options.model
    channel_name = options.channel
    detector_name = options.detector
    pipeline_name = options.pipeline
    #input_format = options.format
    #ds_name = options.name
    #add_noise = options.noise
    #tmin = options.tmin
    #tmax = options.tmax
    #make_spectrogram = options.spectrogram
    #archive = options.archive
    #ratio_split = options.ratiosplit
    #summary_metadata_filename = options.metadata
    #proc_method = options.proc
    #downsample_frequency = options.downsample

    config_filename = args[0]

    #####################################################

    start_time = str(time.strftime("%y/%m/%d at %H:%M:%S", time.localtime()))

    # First, check the config file
    if (config_filename is None) or not os.path.exists(config_filename):
        print("Config file not found!. Exit")
        sys.exit(1)

    config_parameters = read_json_file(config_filename)

    # create the output dir
    if output_dir is None:
        output_dir = os.path.join(work_dir,"djuploader")

    log_dir = os.path.join(output_dir,"log")
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
        os.mkdir(log_dir)

    # INIT the logger
    up_logger = CustomLogger("loader", m_file_logging=logging, m_log_dir=log_dir)
    loglevel = None
    if debug_mode:
        loglevel = "DEBUG"
    else:
        loglevel = "INFO"


    up_logger.setLevel(loglevel)


    up_logger.info('\n\n**************************************')
    up_logger.info("    " + str(script_name))
    up_logger.info("     (Running on " + os_system + " OS)")
    up_logger.info('**************************************')
    up_logger.info("Start time " + str(start_time))

    # List parameters and args
    up_logger.info('\nInput options:')
    for key, val in iter(parser.values.__dict__.items()):
        up_logger.info(key + ": " + str(val))

    up_logger.info("Work directory " + work_dir)
    up_logger.info("Output directory " + output_dir)


    #read the input
    #data_df = pd.read_hdf(input_filename)
    data_df = pd.read_csv(input_filename)
    up_logger.info("Data contains "+str(len(data_df))+ " data entries")

    #Init django
    sys.path.append(os.path.dirname(script_path))
    os.environ['DJANGO_SETTINGS_MODULE'] = config_parameters["PROJECT_NAME"]+'.settings'
    up_logger.debug("Django settings loaded to " +os.environ['DJANGO_SETTINGS_MODULE'])
    django.setup()
    from monitor.models import Channel,Detector,GlitchInstance,Pipeline,OutputDirectory,GlitchClass
    from django.contrib.auth.models import User

    colnames = data_df.columns.values.tolist()
    ndata=0
    print('Accepted metadata:', colnames)
    for di in range(len(data_df)):
        created=False
        col_names = data_df.columns
        label_name=None
        #print(col_names[0][4])
        #sys.exit(9)
        if model_name=="Channel":
            detector_code = data_df["detector_id"][di]
            m_detector = Detector.objects.get(code=detector_code)
            #print(m_detector,m_detector.id)
            #sys.exit(9)
            #print(detector_code)
            new_add, created = Channel.objects.get_or_create(name=data_df["name"][di],detector_id=m_detector.id,description=data_df["description"][di])
            #new_add, created = Channel.objects.get_or_create(name=data_df["name"][di],description=data_df["description"][di])
            #print(m_detector)
            #sys.exit(9)

            #if created:
            #    ndata+=1
            #    up_logger.info(model_name+ " loaded: "+data_df["name"][di])
            #else:
            #    up_logger.warning(model_name+ " "+data_df["name"][di]+" already present. Skip!")
            label_name=data_df["detector_id"][di]+" "+data_df["name"][di]
        elif model_name=="Detector":
            new_add, created = Detector.objects.get_or_create(code=data_df["code"][di],\
                                                              name=data_df["name"][di], \
                                                              latitude=data_df["latitude"][di], \
                                                              longitude=data_df["longitude"][di], \
                                                              description=data_df["description"][di])
            label_name=data_df["name"][di]
        elif model_name == "GlitchInstance":  
            m_detector = Detector.objects.get(Q(code=detector_name))
            #print(channel_name)
            #print(m_detector.id)
            m_channel = Channel.objects.get(Q(name=channel_name) & Q(detector_id = m_detector.id))
            m_pipeline = Pipeline.objects.get(Q(name=pipeline_name))

            #look for directory
            main_output_dir  = output_dir
            main_output_dir=os.path.join(main_output_dir,"*")
            main_output_dir=os.path.join(main_output_dir,channel_name)
            m_outdir_id=None
            data_out_dir = glob.glob(os.path.join(main_output_dir,str(int(round(data_df["GPStime"][di])))))
            note_comment = str(time.strftime("Added on %y-%m-%d at %H:%M:%S UTC", time.localtime()))
            #print(data_out_dir,os.path.join(main_output_dir,str(round(data_df["GPStime"][di]))))

            #check if glitch exist already...
            existing_glitch=None
            try:
                existing_glitch = GlitchInstance.objects.get(peak_time_gps=data_df["GPStime"][di], \
                                                                        channel_id=m_channel.id, \
                                                                        glitch_pipeline_id=m_pipeline.id, \
                                                                        #notes=note_comment, \
                                                                        duration=data_df["duration"][di], \
                                                                        peak_frequency=data_df["peakFreq"][di], \
                                                                        bandwidth=data_df["bandwidth"][di], \
                                                                        snr=data_df["snr"][di])
            except ObjectDoesNotExist:
                pass

            if existing_glitch is None:
                if len(data_out_dir) > 0:
                    up_logger.info("Directory %s found!" % data_out_dir[0])
                    data_out_dir = os.path.basename(os.path.dirname(os.path.dirname(data_out_dir[0])))
                    m_outdir = OutputDirectory.objects.get(Q(name=data_out_dir))
                    #print("rr", m_outdir, data_out_dir)
                    new_add, created = GlitchInstance.objects.get_or_create(peak_time_gps=data_df["GPStime"][di], \
                                                                            channel_id=m_channel.id, \
                                                                            output_dir_id=m_outdir.id, \
                                                                            glitch_pipeline_id=m_pipeline.id, \
                                                                            notes=note_comment, \
                                                                            duration=data_df["duration"][di], \
                                                                            peak_frequency=data_df["peakFreq"][di], \
                                                                            bandwidth=data_df["bandwidth"][di], \
                                                                            snr=data_df["snr"][di])
                    # sys.exit(0)
                else:
                    new_add, created = GlitchInstance.objects.get_or_create(peak_time_gps=data_df["GPStime"][di], \
                                                                            channel_id=m_channel.id, \
                                                                            glitch_pipeline_id=m_pipeline.id, \
                                                                            notes=note_comment, \
                                                                            duration=data_df["duration"][di], \
                                                                            peak_frequency=data_df["peakFreq"][di], \
                                                                            bandwidth=data_df["bandwidth"][di], \
                                                                            snr=data_df["snr"][di])
                label_name = str(data_df["GPStime"][di])
            else:
                label_name = str(existing_glitch)
                #up_logger.warning("Glitch %s existing. Skip upload!" % str(existing_glitch))
            #sys.exit(9)
        elif model_name=="Pipeline":
            label_name=data_df["name"][di]
            new_add, created = Pipeline.objects.get_or_create(name=data_df["name"][di], \
                                                              pipeline_type=data_df["pipeline_type"][di], \
                                                              out_directory=data_df["out_directory"][di], \
                                                              description=data_df["description"][di], \
                                                              setup_command=data_df["setup_command"][di], \
                                                              list_command=data_df["list_command"][di], \
                                                              run_command=data_df["run_command"][di])
        elif model_name=="OutputDirectory":
            new_add, created = OutputDirectory.objects.get_or_create(name=data_df["datename"][di])
            label_name = str(data_df[str(col_names[0])][di])
        elif model_name == "User":
            label_name = data_df["username"][di]
            user = User.objects.create_user(username=data_df["username"][di],\
                                            first_name=data_df["first_name"][di], \
                                            last_name=data_df["last_name"][di],\
                                            email=data_df["email"][di],\
                                            password = data_df["password"][di],\
                                            is_staff=True)
            user.save()
        elif model_name=="GlitchClass":
            label_name=data_df["name"][di]
            new_add, created = GlitchClass.objects.get_or_create(code=data_df["code"][di], \
                                                              name=data_df["name"][di],\
                                                              description=data_df["description"][di])
        #sys.exit(9)
        if created:
            ndata+=1
            up_logger.info(model_name+ " loaded: "+label_name)
        else:
            up_logger.warning(model_name+" "+label_name+" already present. Skip!")
        #sys.exit(9)

    up_logger.info(str(ndata)+" new elements uploaded!")
