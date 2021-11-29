#!/usr/bin/env python
import optparse
import os
import django
   
parser = optparse.OptionParser()
parser.add_option("--gpsstart", default=None, type=float)
parser.add_option("--gpsend", default=None, type=float)
parser.add_option("--channel", default="V1:Hrec_hoft_16384Hz", type=str)
parser.add_option("--set", default='local', type=str)
parser.add_option("--pipeline", default='Omicron', type=str)
parser.add_option("--gclass", default=None, type=str)
    
(options, args) = parser.parse_args()
    
gpsstart = options.gpsstart
gpsend = options.gpsend
channel_ = options.channel
pipeline_ = options.pipeline
set_ = options.set
class_ = options.gclass 
    
if set_.startswith('staging'):
    set_, run = set_.split(':')
if set_ == 'local':
    run = set_
 
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "virgo_glitches.settings.{}".format(set_))

django.setup()

#from django.core.management import call_command

import pandas as pd
import pathlib
import json

from django.conf import settings
from vini_db_connection import DBload 
#settings.configure()
base_conf_dir = ''
for i in os.getenv('PATH').split(':'):
    if i.endswith('virgo_glitches') or i.endswith('vini'):
        base_conf_dir=i

if 'staging' in str(settings): 
   base_conf_dir = "/var/www/html/reinforce/virgo_glitches" 
            
# Set location of the data which will be migrated            
    
def upload_glitches(file_path, gps_min=None, gps_max=None, 
                    channel="V1:Hrec_hoft_16384Hz", 
                    pipeline_name="Omicron", class_name=None,
                    mode='local'):
    """
    """
    print('Glitches uploading started!')
    glitches_load = DBload(mode)
    dcode, cname = tuple(channel.split(':'))
    # Insert detector
    did = glitches_load.get_detector_id(dcode)
    if did is None:
        with open(os.path.join(base_conf_dir, 'data', 'list_detectors.json')) as jf:
            dets = json.load(jf) 
            glitches_load.insert_detector(**dets[dcode])
        did = glitches_load.get_detector_id(dcode)
        print('{} added to detectors!'.format(dcode))    
    # Insert channel        
    cid = glitches_load.get_channel_id(did, cname)        
    if cid is None:
        with open(os.path.join(base_conf_dir, 'data', 'list_channels.json')) as jf:
            chans = json.load(jf) 
            glitches_load.insert_channel(did, **chans[cname])
        print('{} added to channels!'.format(cname))    
    # Insert pipeline        
    pid = glitches_load.get_pipeline_id(pipeline_name)        
    if pid is None:
        with open(os.path.join(base_conf_dir, 'data', 'list_pipelines.json')) as jf:
            pipes = json.load(jf) 
            glitches_load.insert_pipeline(**pipes[pipeline_name])
        print('{} added to pipelines!'.format(pipeline_name))  
    if class_name is not None:
        # Insert class        
        clid = glitches_load.get_class_id(class_name)        
        if clid is None:
            with open(os.path.join(base_conf_dir, 'data', 'list_classes.json')) as jf:
                classes = json.load(jf) 
                glitches_load.insert_class(**classes[class_name])
            print('{} added to classes!'.format(class_name))        
    # Import glitches                     
    glitches_load.load_file(file_path, gps_min, gps_max, channel, 
                            pipeline_name, class_name)
    print('Glitches uploading done!') 
    del glitches_load                       
          

def get_directory(files_type):
    if files_type=='csv':
        directory = os.path.join(base_conf_dir, 'data', 'ListGlitchMetadata')
    if files_type=='json':
        directory = os.path.join(base_conf_dir, 'data', 'ApiJsonFiles')   

    return directory  
    
#from monitor.models import GlitchInstance, GlitchClass, Channel, Detector, Pipeline 

# This must be adapted to new pandas dataframe migration 
def fill_O1_O2_O3a(apps, schema_editor, file_s='*', file_t='csv'):

    GlitchInstance = apps.get_model('monitor', 'GlitchInstance')
    GlitchClass = apps.get_model('monitor', 'GlitchClass')
    Channel = apps.get_model('monitor', 'Channel')
    Detector = apps.get_model('monitor', 'Detector')
    Pipeline = apps.get_model('monitor', 'Pipeline')
    print('Migration started!')

    # This is a test, the same 'No Pipeline' for all glitches
    if file_t=='csv':
        pipl, created = Pipeline.objects.get_or_create(name='GravitySpy', 
               pipeline_type='NoType', 
               out_directory=' ', 
               description='Pipeline that generated the glitch.', 
               setup_command=' ', list_command=' ', run_command=' ')
        if created:
            #print('Pipeline saved')
            pipl.save()
    directory = get_directory(file_t)
    for filepath in pathlib.Path(directory).glob('**/{}'.format(file_s)):
        abs_filepath = filepath.absolute()
        print('Importing glitches from {}'.format(abs_filepath))
        
        if file_t=='csv':
            data_df = pd.read_csv(abs_filepath)
        if file_t=='json':
            data_df = pd.read_json(abs_filepath)
            #data_dict = json.loads(open(abs_filepath).read())
            
        for di in range(len(data_df)):
            #print('AAAAAAAAAAAA', data_df["label"][di])
            #print('BBBBBBBBBBBB', data_df["ifo"][di])
            if data_df["ifo"][di] == 'H1':
                d_name = 'LIGO Hanford interferometer'
                d_description = 'LIGO Hanford interferometer'
                latitude = 46.45
                longitude = 119.41
                main_ch_name = 'GPD-CALIB_STRAIN'
            if data_df["ifo"][di] == 'L1':
                d_name = 'LIGO Livingston interferometer'
                d_description = 'LIGO Livingston interferometer' 
                latitude = 30.56
                longitude = 90.77 
                main_ch_name = 'GPD-CALIB_STRAIN'  
            if data_df["ifo"][di] == 'V1':
                d_name = 'Virgo interferometer'
                d_description = 'Virgo interferometer' 
                latitude = 43.63
                longitude = -10.5   
                main_ch_name = 'Hrec_hoft_16384Hz' 
            new_d, created = Detector.objects.get_or_create(code=data_df["ifo"][di],
                                                          name=d_name, 
                                                          latitude=latitude, 
                                                          longitude=longitude, 
                                                          description=d_description)
            #print('AL DETECTOR CI ARRIVA.')
            if created:
                #print('Detector saved.')
                new_d.save()   
            
            if file_t=='csv':
                ch_description = 'Main channel of the interferomenter, where the gravitational strain is reconstructed from the differential lenght of the arms.'
                new_c, created = Channel.objects.get_or_create(name=main_ch_name, 
                                                               detector=new_d,
                                                               description=ch_description)
            if file_t=='json':
                ch_description = data_df["channel_description"]
                new_c, created = Channel.objects.get_or_create(name=data_df["channel_name"], 
                                                               detector=new_d,
                                                               description=ch_description)                                                   
                                       
            if created:
                #print('Channel saved.')
                new_c.save()
            #print('IL code è uguale a ', data_df["label"][di])
            #print(GlitchClass.objects.get(pk=1).code)
            new_gc, created = GlitchClass.objects.get_or_create(code=data_df["label"][di][:5], 
                                                               name=data_df["label"][di], 
                                                               description='Name of the family at which the glitch belongs to.')
            #print('ALLA CLASSE CI ARRIVA.')
            if created:
                #print('Class saved.')
                new_gc.save()             
            new_gi, created = GlitchInstance.objects.get_or_create(glitch_class=new_gc,
                                                                  channel=new_c, 
                                                                  glitch_pipeline=pipl,
                                                                  notes = 'This is part of the O1, O2, O3a glitches of GravitySpy.',
                                                                  peak_time_gps=data_df["GPStime"][di], 
                                                                  duration=data_df["duration"][di], 
                                                                  peak_frequency=data_df["peakFreq"][di], 
                                                                  bandwidth=data_df["bandwidth"][di], 
                                                                  snr=data_df["snr"][di])
            if created: 
                #print('Glitch saved.')                                                     
                new_gi.save()
        print('Loading terminated!')
    print('Migration done!')

if __name__=='__main__':
   # Per tutto usa upload_glitches, se qualcosa mancherà verrà aggiunto automaticamente
    
    if set_.startswith('staging'):
        set_, run = set_.split(':')
    if set_ == 'local':
        run = set_
 
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "virgo_glitches.settings.{}".format(set_))

    django.setup()
       
    #file_p = "/opt/w3/DataAnalysis/GeOmiTri/O3_full.h5"
    #gps_min=1256655618
    #gps_max=1269363618
    #channel_="V1:Hrec_hoft_16384Hz"
    #run="O3b"  
    file_p = args[0]
    upload_glitches(file_p, gpsstart, gpsend, channel=channel_, 
                                              pipeline_name=pipeline_,
                                              class_name=class_,
                                              mode=run)
    
    
