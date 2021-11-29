import imp
import logging
import time
import pymysql

import pandas as pd
import numpy as np

#import Constants
#import gpstime
#import Tools

log = logging.getLogger()
log.setLevel(logging.DEBUG)

class DBload:
    '''
    Data base loading module.
    All connections to the database are made via this class.
    '''
    ######################
    # CONNECTION METHODS #
    ######################
    def __init__(self, db='local'):
        '''
        Establish DB connection.
        '''
        # Instantiate objects.
        if db == 'local':  
            from virgo_glitches.settings.local import DATABASES
            DATABASE = DATABASES['default']
        elif db == 'staging':  
            from virgo_glitches.settings.staging import DATABASES
            DATABASE = DATABASES['default']
        elif db == 'O2':
            from virgo_glitches.settings.staging import DATABASES
            DATABASE = DATABASES['O2']
        elif db == 'O3a':
            from virgo_glitches.settings.staging import DATABASES
            DATABASE = DATABASES['O3a']
        elif db == 'O3b':
            from virgo_glitches.settings.staging import DATABASES
            DATABASE = DATABASES['O3b']
        else:
            raise ValueError("**Settings mode not found!**")
        # Attempt connection.           
        try:
            # Attempt DB connection.
            self.cnxn = pymysql.connect(host=DATABASE['HOST'], 
                                        user=DATABASE['USER'], 
                                        password=DATABASE['PASSWORD'],
                                        db=DATABASE['NAME'],
                                        cursorclass=pymysql.cursors.DictCursor)
        except pymysql.OperationalError as e:
            # Log event.
            full_err_msg = '** Problem establishing database connection: ' + str(e)
            log.error(full_err_msg)
            raise Exception(full_err_msg)
    
    def __del__(self):
        '''
        Close DB connection.
        '''
        # If connection exists.
        try:
            self.cnxn
        except:
            # Log event.
            log.warning('** Database connection has already closed.')
        else:
            # Close
            try:
                self.cnxn.close()
            except:
                # Log event.
                full_err_msg = '** Problem closing database connection.'
                log.error(full_err_msg)
                raise Exception(full_err_msg)
                
    ###################
    # INSERT GLITCHES #
    ###################            
    def insert_glitches(self, glitches_df, channel_id, pipeline_id, 
                        class_id=None):
        '''
        Insert glitches given in pandas data frame format.
        '''
        # Init.
        err_msg = 'inserting glitches pandas data frame.'
        try:
            # Set DB cursor.
            cur = self.cnxn.cursor()
        except pymysql.OperationalError as e:
            # Log event.
            full_err_msg = '**** Problem ' + err_msg + '. Unable to create cursor on database connection: ' + str(e)
            log.error(full_err_msg)
            raise Exception(full_err_msg)
        else:
            try:
                # Get.
                cur.executemany("""
                            INSERT INTO monitor_glitchinstance
                            (glitch_class_id, channel_id, glitch_pipeline_id, 
                            peak_time_gps, duration, peak_frequency, bandwidth,
                            snr, notes)
                            VALUES
                            (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, glitches_df.values.tolist())      
                # Commit.
                self.cnxn.commit()
            except pymysql.OperationalError as e:
                # Log event.
                full_err_msg = '**** Problem ' + err_msg + '. Unable to execute SQL statement: ' + str(e)
                log.error(full_err_msg)
                raise Exception(full_err_msg) 
                
    ###################
    # DELETE GLITCHES #
    ###################            
    def delete_glitches(self, gps_min, gps_max, channel_name=None, 
                        pipeline_name=None):
        '''
        Delete the glitches in a given time interval.
        '''
        # Init.
        err_msg = 'inserting time intervals.'
        where_query = "peak_time_gps>={} and peak_time_gps<={}".format(gps_min, gps_max)
        if channel_name is not None:
            det_code, ch_name = tuple(channel_name.split(':'))
            det_id = self.get_detector_id(det_code)
            ch_id = self.get_channel_id(det_id, ch_name)
            where_query += " and channel_id={}".format(ch_id)
        if pipeline_name is not None:
            pip_id = self.get_pipeline_id(pipeline_name)
            where_query += " and glitch_pipeline_id={}".format(pip_id)
        try:
            # Set DB cursor.
            cur = self.cnxn.cursor()
        except pymysql.OperationalError as e:
            # Log event.
            full_err_msg = '**** Problem ' + err_msg + '. Unable to create cursor on database connection: ' + str(e)
            log.error(full_err_msg)
            raise Exception(full_err_msg)
        else:
            try:
                # Get.
                cur.execute("DELETE FROM monitor_glitchinstance WHERE {}".format(where_query))    
                # Commit.
                self.cnxn.commit()
            except pymysql.OperationalError as e:
                # Log event.
                full_err_msg = '**** Problem ' + err_msg + '. Unable to execute SQL statement: ' + str(e)
                log.error(full_err_msg)
                raise Exception(full_err_msg)
                
    ################
    # GET GLITCHES #
    ################            
    def get_glitches(self, gps_min, gps_max=None, frequency_min=None,  
                     frequency_max=None, snr_min=None, snr_max=None,
                     duration_min=None, duration_max=None,
                     bandwidth_min=None, bandwidth_max=None,  
                     channel_name=None, pipeline_name=None, class_name=None):
        '''
        Delete the glitches in a given time interval.
        '''
        # Init.
        err_msg = 'inserting metadata intervals intervals.'
        where_query = "peak_time_gps>={}".format(gps_min)
        if gps_max is not None:
            where_query += " and peak_time_gps<={}".format(gps_max)
        if frequency_min is not None:
            where_query += " and peak_frequency>={}".format(frequency_min)            
        if frequency_max is not None:
            where_query += " and peak_frequency<={}".format(frequency_max)
        if snr_min is not None:
            where_query += " and snr>={}".format(snr_min)            
        if snr_max is not None:
            where_query += " and snr<={}".format(snr_max) 
        if duration_min is not None:
            where_query += " and duration>={}".format(duration_min)             
        if duration_max is not None:
            where_query += " and duration<={}".format(duration_max) 
        if bandwidth_min is not None:
            where_query += " and bandwidth>={}".format(bandwidth_min)             
        if bandwidth_max is not None:
            where_query += " and bandwidth<={}".format(bandwidth_max) 
                                                       
        if channel_name is not None:
            if isinstance(channel_name, str):
                det_code, ch_name = tuple(channel_name.split(':'))
                det_id = self.get_detector_id(det_code)
                ch_id = self.get_channel_id(det_id, ch_name)
                where_query += " and channel_id={}".format(ch_id)  
            if isinstance(channel_name, list):
                channels_ids = []
                for ch in channel_name:
                    if ':' in ch:
                        det_code, ch_name = tuple(ch.split(':'))
                        det_id = self.get_detector_id(det_code)
                        ch_id = self.get_channel_id(det_id, ch_name)
                        channels_ids.append(ch_id)
                    else:
                         det_id = self.get_detector_id('V1')
                         ch_id = self.get_channel_id(det_id, ch)  
                         channels_ids.append(ch_id) 
                if len(channels_ids)==1: 
                    where_query += " and channel_id={}".format(channels_ids[0]) 
                else: 
                    where_query += " and (channel_id={}".format(channels_ids[0]) 
                    for id_ in channels_ids[1:]:  
                        where_query += " or channel_id={}".format(id_)                                                   
                    where_query += ")"  
                                           
        if pipeline_name is not None:
            if isinstance(pipeline_name, str):        
                pip_id = self.get_pipeline_id(pipeline_name)
                where_query += " and glitch_pipeline_id={}".format(pip_id)
            if isinstance(pipeline_name, list):
                pipelines_ids = [] 
                for pl in pipeline_name:
                    pip_id = self.get_pipeline_id(pl)
                    pipelines_ids.append(pip_id) 
                if len(pipelines_ids)==1: 
                    where_query += " and glitch_pipeline_id={}".format(pipelines_ids[0]) 
                else: 
                    where_query += " and (glitch_pipeline_id={}".format(pipelines_ids[0]) 
                    for id_ in pipelines_ids[1:]:  
                        where_query += " or glitch_pipeline_id={}".format(id_)                                                   
                    where_query += ")"                      
                                               
        if class_name is not None:
            if isinstance(class_name, str): 
                if class_name=='NONE':  
                    where_query += " and glitch_class_id IS NULL"
                else:          
                    cls_id = self.get_class_id(class_name)
                    where_query += " and glitch_class_id={}".format(cls_id)
            if isinstance(class_name, list):
                classes_ids = [] 
                for cl in class_name:
                    if cl=='NONE': 
                        classes_ids.append('NONE')
                    else:    
                        cls_id = self.get_class_id(cl)
                        classes_ids.append(cls_id)   
                if len(classes_ids)==1: 
                    if 'NONE'==classes_ids[0]: 
                        where_query += " and glitch_class_id IS NULL"
                    else:    
                        where_query += " and glitch_class_id={}".format(classes_ids[0]) 
                else:
                    if 'NONE' in classes_ids: 
                        classes_ids.remove('NONE')
                        where_query += " and (glitch_class_id={}".format(classes_ids[0]) 
                        for id_ in classes_ids[1:]:  
                            where_query += " or glitch_class_id={}".format(id_)                                                   
                        where_query += " or glitch_class_id IS NULL)" 
                    else: 
                        where_query += " and (glitch_class_id={}".format(classes_ids[0]) 
                        for id_ in classes_ids[1:]:  
                            where_query += " or glitch_class_id={}".format(id_)
                        where_query += ")"     
        #print('AAA', where_query)                
        try:
            # Set DB cursor.
            cur = self.cnxn.cursor()
        except pymysql.OperationalError as e:
            # Log event.
            full_err_msg = '**** Problem ' + err_msg + '. Unable to create cursor on database connection: ' + str(e)
            log.error(full_err_msg)
            raise Exception(full_err_msg)
        else:
            try:
                # Get.
                import time
                i_time = time.time()    
                cur.execute("""
                            SELECT id, peak_time_gps, peak_frequency, snr, duration, bandwidth,
                                   channel_id, glitch_class_id, glitch_pipeline_id 
                                   FROM monitor_glitchinstance WHERE {}
                                   """.format(where_query))
                e_time = time.time() 
                print('CHECK time execute {} s'.format(e_time-i_time))
                g_df = pd.DataFrame(cur.fetchall())                          
            except pymysql.OperationalError as e:
                # Log event.
                full_err_msg = '**** Problem ' + err_msg + '. Unable to execute SQL statement: ' + str(e)
                log.error(full_err_msg)
                raise Exception(full_err_msg)
        #print('dataset empty', g_df.empty)
        if g_df.empty:
            return g_df
        #f_time = time.time()
        #print('CHECK time df {} s'.format(f_time-e_time)) 
        # Return names instead of ids  
        ch_list = tuple(list(g_df['channel_id']))
        ch_list = sorted(list(dict.fromkeys(ch_list)))
        pl_list = list(g_df['glitch_pipeline_id'])
        pl_list = sorted(list(dict.fromkeys(pl_list)))
        cl_list = list(g_df['glitch_class_id'])
        cl_list = sorted(list(dict.fromkeys(cl_list)))
        # prepare detector
        g_df['detector_id'] = g_df['channel_id']
        cur.execute("SELECT detector_id FROM monitor_channel WHERE id IN %s", (ch_list, ))
        det_list = cur.fetchall() 
        det_list = [list(det_list[i].values())[0] for i in range(len(det_list))] 
        g_df['detector_id'].replace(ch_list, det_list, inplace=True) 
        det_list = sorted(list(dict.fromkeys(det_list)))
        # detector preprocessing
        cur.execute("SELECT code FROM monitor_detector WHERE id IN %s", (det_list, ))
        sdet_list = cur.fetchall() 
        sdet_list = [list(sdet_list[i].values())[0] for i in range(len(sdet_list))] 
        #print('aaa', det_list, 'bbb', sdet_list)
        g_df['detector_id'].replace(det_list, sdet_list, inplace=True)
        g_df.rename(columns={'detector_id':'channel__detector__code'}, inplace=True)                            
        # channel processing
        cur.execute("SELECT name FROM monitor_channel WHERE id IN %s", (ch_list, ))
        sch_list = cur.fetchall()
        sch_list = [list(sch_list[i].values())[0] for i in range(len(sch_list))] 
        g_df['channel_id'].replace(ch_list, sch_list, inplace=True)
        g_df.rename(columns={'channel_id':'channel__name'}, inplace=True)   
        # pipeline processing
        cur.execute("SELECT name FROM monitor_pipeline WHERE id IN %s", (pl_list, ))
        spl_list = cur.fetchall()
        spl_list = [list(spl_list[i].values())[0] for i in range(len(spl_list))]
        g_df['glitch_pipeline_id'].replace(pl_list, spl_list, inplace=True)
        g_df.rename(columns={'glitch_pipeline_id':'glitch_pipeline__name'}, inplace=True)  
        # class processing
        cur.execute("SELECT name FROM monitor_glitchclass WHERE id IN %s", (cl_list, ))
        scl_list = cur.fetchall()
        scl_list = [list(scl_list[i].values())[0] for i in range(len(scl_list))]
        if None in cl_list:
            scl_list += [None]	
        #print('aaaaa\n', cl_list)
        #print('bbbbb\n', scl_list)	
        g_df['glitch_class_id'].replace(cl_list, scl_list, inplace=True)
        g_df.rename(columns={'glitch_class_id':'glitch_class__name'}, inplace=True)                
        return g_df   
        
    ##################
    # COUNT GLITCHES #
    ##################
    def count_glitches(self, where_query=''):
        # Init.
        err_msg = 'Counting glitches in the table'
        try:
            # Set DB cursor.
            cur = self.cnxn.cursor()
        except pymysql.OperationalError as e:
            # Log event.
            full_err_msg = '**** Problem ' + err_msg + '. Unable to create cursor on database connection: ' + str(e)
            log.error(full_err_msg)
            raise Exception(full_err_msg)
        else:
            try:
                # Get.
                cur.execute("SELECT count(*) FROM monitor_glitchinstance {}".format(where_query))
                gl_count = cur.fetchone()                            
            except pymysql.OperationalError as e:
                # Log event.
                full_err_msg = '**** Problem ' + err_msg + '. Unable to execute SQL statement: ' + str(e)
                log.error(full_err_msg)
                raise Exception(full_err_msg)
        return gl_count['count(*)']                                      
                
    ###############
    # GET CHANNEL #
    ###############
    def get_channel_id(self, detector_id, channel_name):
        # Init.
        err_msg = 'Looking for channel id!'
        try:
            # Set DB cursor.
            cur = self.cnxn.cursor()
        except pymysql.OperationalError as e:
            # Log event.
            full_err_msg = '**** Problem ' + err_msg + '. Unable to create cursor on database connection: ' + str(e)
            log.error(full_err_msg)
            raise Exception(full_err_msg)
        else:
            try:
                # Get.
                cur.execute("SELECT id FROM monitor_channel WHERE name='{}' and detector_id={}".format(channel_name, detector_id))
                ch_id = cur.fetchone()                            
            except pymysql.OperationalError as e:
                # Log event.
                full_err_msg = '**** Problem ' + err_msg + '. Unable to execute SQL statement: ' + str(e)
                log.error(full_err_msg)
                raise Exception(full_err_msg)
        try:        
            return ch_id['id'] 
        except TypeError:
            return ch_id                   
                
    ################
    # GET DETECTOR #
    ################     
    def get_detector_id(self, detector_code):
        # Init.
        err_msg = 'Looking for detector id!'
        try:
            # Set DB cursor.
            cur = self.cnxn.cursor()
        except pymysql.OperationalError as e:
            # Log event.
            full_err_msg = '**** Problem ' + err_msg + '. Unable to create cursor on database connection: ' + str(e)
            log.error(full_err_msg)
            raise Exception(full_err_msg)
        else:
            try:
                # Get.
                cur.execute("SELECT id FROM monitor_detector WHERE code='{}'".format(detector_code))
                det_id = cur.fetchone()                          
            except pymysql.OperationalError as e:
                # Log event.
                full_err_msg = '**** Problem ' + err_msg + '. Unable to execute SQL statement: ' + str(e)
                log.error(full_err_msg)
                raise Exception(full_err_msg)
        try:        
            return det_id['id']
        except TypeError:
            return det_id               
                
    ################
    # GET PIPELINE #
    ################                
    def get_pipeline_id(self, pipeline_name):
        # Init.
        err_msg = 'Looking for pipeline id!'
        try:
            # Set DB cursor.
            cur = self.cnxn.cursor()
        except pymysql.OperationalError as e:
            # Log event.
            full_err_msg = '**** Problem ' + err_msg + '. Unable to create cursor on database connection: ' + str(e)
            log.error(full_err_msg)
            raise Exception(full_err_msg)
        else:
            try:
                # Get.
                cur.execute("SELECT id FROM monitor_pipeline WHERE name='{}'".format(pipeline_name))
                pipl_id = cur.fetchone()                            
            except pymysql.OperationalError as e:
                # Log event.
                full_err_msg = '**** Problem ' + err_msg + '. Unable to execute SQL statement: ' + str(e)
                log.error(full_err_msg)
                raise Exception(full_err_msg)
        try: 
            return pipl_id['id']
        except TypeError: 
            return pipl_id          

    #############
    # GET CLASS #
    #############                
    def get_class_id(self, class_name):
        # Init.
        err_msg = 'Looking for class id!'
        try:
            # Set DB cursor.
            cur = self.cnxn.cursor()
        except pymysql.OperationalError as e:
            # Log event.
            full_err_msg = '**** Problem ' + err_msg + '. Unable to create cursor on database connection: ' + str(e)
            log.error(full_err_msg)
            raise Exception(full_err_msg)
        else:
            try:
                # Get.
                cur.execute("SELECT id FROM monitor_glitchclass WHERE name='{}'".format(class_name))
                cls_id = cur.fetchone()                            
            except pymysql.OperationalError as e:
                # Log event.
                full_err_msg = '**** Problem ' + err_msg + '. Unable to execute SQL statement: ' + str(e)
                log.error(full_err_msg)
                raise Exception(full_err_msg)
        try: 
            return cls_id['id']
        except TypeError: 
            return cls_id                                                                     
                            
    ###################################
    # IMPORT GLITCHES FROM HDF5 FILES #
    ###################################
    def load_file(self, file_path, gps_min=None, gps_max=None, 
                  channel="V1:Hrec_hoft_16384Hz", 
                  pipeline_name="Omicron", class_name=None):
        """
        """
        
        detcode, ch_name = tuple(channel.split(':'))
        
        # Query set
        where_query = None
        if gps_min is not None and gps_max is not None:
            where_query="index>={} and index<={}".format(gps_min, gps_max)
        if gps_min is not None and gps_max is None:
            where_query="index>={}".format(gps_min)
        if gps_min is None and gps_max is not None:
            where_query="index<={}".format(gps_max)

        # Get ids
        det_id = self.get_detector_id(detcode) 
        ch_id = self.get_channel_id(det_id, ch_name)
        pipl_id = self.get_pipeline_id(pipeline_name)
        if class_name is None:
            cls_id = None
        if class_name is not None:
            cls_id = self.get_class_id(class_name)
        
        # Reprocessing metadata
        try:
            data_df = pd.read_hdf(file_path, ch_name, where=where_query)
        except KeyError:
            data_df = pd.read_hdf(file_path, 'df_sources_parameters', where=where_query)
        data_df['glitch_class_id'] = np.full(len(data_df), cls_id) 
        data_df['channel_id'] = np.full(len(data_df), ch_id)
        data_df['glitch_pipeline_id'] = np.full(len(data_df), pipl_id)
        data_df['bandwidth'] = data_df['f_end']-data_df['f_start']
        data_df['peak_frequency'] = data_df['f_peak']
        data_df['peak_time_gps'] = data_df.index
        #data_df['id'] = np.linspace(1, len(data_df),len(data_df), dtype=int)
        data_df['notes'] = np.full(len(data_df['peak_time_gps']), 'This is an {} trigger'.format(pipeline_name))
        columns_list = ['glitch_class_id', 'channel_id', 'glitch_pipeline_id',
                        'peak_time_gps', 'duration', 'peak_frequency', 
                        'bandwidth', 'snr', 'notes']
        data_df = data_df[columns_list]
        #print("AAAAAAAAAAAAA\n", data_df, len(data_df))
      
        self.insert_glitches(data_df, channel_id=ch_id, 
                             pipeline_id=pipl_id, class_id=cls_id)    
        
    ###################
    # INSERT DETECTOR #
    ###################
    def insert_detector(self, **kwargs):
        '''
        Insert the parameters passed at the start of the run.
        '''
        # Init.
        err_msg = 'inserting run-start parameters'
        try:
            # Set DB cursor.
            cur = self.cnxn.cursor()
        except pymysql.OperationalError as e:
            # Log event.
            full_err_msg = '**** Problem ' + err_msg + '. Unable to create cursor on database connection: ' + str(e)
            log.error(full_err_msg)
            raise Exception(full_err_msg)
        else:
            try:
                # Get.
                cur.execute("""
                            INSERT INTO monitor_detector
                            (code, name, latitude, longitude, description)
                            VALUES
                            (%(code)s, %(name)s, %(latitude)s, 
                             %(longitude)s, %(description)s)
                            """, {'code' : kwargs['code'], #Questi valori delle chiavi cambieranno a seconda di come 
                                  'name' : kwargs['name'], # sono scritti in omicron
                                  'latitude' : str(kwargs['latitude']), # per ora metti tutto come nel database
                                  'longitude' : str(kwargs['longitude']),
                                  'description' : kwargs['description']})

                # Commit.
                self.cnxn.commit()
            except pymysql.OperationalError as e:
                # Log event.
                full_err_msg = '**** Problem ' + err_msg + '. Unable to execute SQL statement: ' + str(e)
                log.error(full_err_msg)
                raise Exception(full_err_msg)
                
    ###################
    # INSERT PIPELINE #
    ###################
    def insert_pipeline(self, **kwargs):
        '''
        Insert the parameters passed at the start of the run.
        '''
        # Init.
        err_msg = 'inserting run-start parameters'
        try:
            # Set DB cursor.
            cur = self.cnxn.cursor()
        except pymysql.OperationalError as e:
            # Log event.
            full_err_msg = '**** Problem ' + err_msg + '. Unable to create cursor on database connection: ' + str(e)
            log.error(full_err_msg)
            raise Exception(full_err_msg)
        else:
            try:
                # Get.
                cur.execute("""
                            INSERT INTO monitor_pipeline
                            (name, pipeline_type, out_directory, description, 
                             setup_command, list_command, run_command)

                            VALUES
                            (%(name)s, %(pipeline_type)s, %(out_directory)s, 
                             %(description)s, %(setup_command)s, %(list_command)s,
                             %(run_command)s)
                            """, {'name' : kwargs['name'],  
                                  'pipeline_type' : kwargs['pipeline_type'], 
                                  'out_directory' : kwargs['out_directory'], 
                                  'description' : kwargs['description'],
                                  'setup_command' : kwargs['setup_command'],
                                  'list_command' : kwargs['list_command'],
                                  'run_command' : kwargs['run_command'],
                           })

                # Commit.
                self.cnxn.commit()
            except pymysql.OperationalError as e:
                # Log event.
                full_err_msg = '**** Problem ' + err_msg + '. Unable to execute SQL statement: ' + str(e)
                log.error(full_err_msg)
                raise Exception(full_err_msg)
                
    ##################
    # INSERT CHANNEL #
    ##################
    def insert_channel(self, detector_id, **kwargs):
        '''
        Insert the parameters passed at the start of the run.
        '''
        # Init.
        err_msg = 'inserting run-start parameters'
        try:
            # Set DB cursor.
            cur = self.cnxn.cursor()
        except pymysql.OperationalError as e:
            # Log event.
            full_err_msg = '**** Problem ' + err_msg + '. Unable to create cursor on database connection: ' + str(e)
            log.error(full_err_msg)
            raise Exception(full_err_msg)
        else:
            try:
                # Get.
                cur.execute("""
                            INSERT INTO monitor_channel
                            (name, detector_id, description)
                            VALUES
                            (%(name)s, %(detector_id)s, %(description)s)
                            """, {'name' : kwargs['name'],  
                                  'detector_id' : detector_id, 
                                  'description' : kwargs['description'],
                           })

                # Commit.
                self.cnxn.commit()
            except pymysql.OperationalError as e:
                # Log event.
                full_err_msg = '**** Problem ' + err_msg + '. Unable to execute SQL statement: ' + str(e)
                log.error(full_err_msg)
                raise Exception(full_err_msg)  
                
    ################
    # INSERT CLASS #
    ################
    def insert_class(self, **kwargs):
        '''
        Insert the parameters passed at the start of the run.
        '''
        # Init.
        err_msg = 'inserting run-start parameters'
        try:
            # Set DB cursor.
            cur = self.cnxn.cursor()
        except pymysql.OperationalError as e:
            # Log event.
            full_err_msg = '**** Problem ' + err_msg + '. Unable to create cursor on database connection: ' + str(e)
            log.error(full_err_msg)
            raise Exception(full_err_msg)
        else:
            try:
                # Get.
                cur.execute("""
                            INSERT INTO monitor_glitchclass
                            (code, name, description)
                            VALUES
                            (%(code)s, %(name)s, %(description)s)
                            """, {'code' : kwargs['code'],  
                                  'name' : kwargs['name'], 
                                  'description' : kwargs['description'],
                           })

                # Commit.
                self.cnxn.commit()
            except pymysql.OperationalError as e:
                # Log event.
                full_err_msg = '**** Problem ' + err_msg + '. Unable to execute SQL statement: ' + str(e)
                log.error(full_err_msg)
                raise Exception(full_err_msg)                               
               
