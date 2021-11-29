import pymysql

# Create a connection object

from django.conf import settings 
 
if 'staging' in str(settings):  
    from virgo_glitches.settings.staging import DATABASES
if 'local' in str(settings):
    from virgo_glitches.settings.local import DATABASES

def query_from_api_db(table='glitchinstance', run='default', fields="*", 
                      queryset=None, channel_n='Hrec_hoft_16384Hz'):

    DATABASE = DATABASES[run]
    connectionObject = pymysql.connect(host=DATABASE['HOST'], 
                                       user=DATABASE['USER'], 
                                       password=DATABASE['PASSWORD'],
                                       db=DATABASE['NAME'],
                                       charset="utf8mb4",
                                    cursorclass=pymysql.cursors.DictCursor)

    try:
        # Create a cursor object
        cursorObject = connectionObject.cursor()  
        
        # Select channel
        chquery = "select * from monitor_channel where name={}".format("'"+channel_n+"'") 
        cursorObject.execute(chquery)
        ch_id = cursorObject.fetchall()[0]['id']
                                           
        # SQL query string
        if queryset is None:
            sqlQuery = "select {} from monitor_{}".format(fields, table)
        else:
            sqlQuery = "select {} from monitor_{} where channel_id={} and {}".format(fields,
                                                                              table,
                                                                              ch_id,
                                                                              queryset)        
    
        # Execute the sqlQuery
        cursorObject.execute(sqlQuery)

        #Fetch all the rows (sorted in time)
        rows = cursorObject.fetchall() 
        rows = sorted(rows, key=lambda k: k["peak_time_gps"])
        
        json_dict = {}
        j_key = 0
        for d in iter(rows):
            del d['id']
            json_dict[j_key] = d
            if 'detector_id' in json_dict[j_key]:
                det_id = json_dict[j_key]['detector_id']
                newquery = "select * from monitor_detector where id={}".format(det_id) 
                cursorObject.execute(newquery)
                det_rows = cursorObject.fetchall()                             
                json_dict[j_key]['detector'] = det_rows[0]['code']                             
                del json_dict[j_key]['detector_id'] 
            if 'channel_id' in json_dict[j_key]:
                ch_id = json_dict[j_key]['channel_id']
                newquery = "select * from monitor_channel where id={}".format(ch_id)
                cursorObject.execute(newquery)
                ch_rows = cursorObject.fetchall() 
                json_dict[j_key]['channel'] = {'name':ch_rows[0]['name'],
                                               'description':ch_rows[0]['description'] }
                newquery = "select * from monitor_detector where id={}".format(ch_rows[0]['detector_id']) 
                cursorObject.execute(newquery)
                det_rows = cursorObject.fetchall()                             
                json_dict[j_key]['detector'] = det_rows[0]['code']                             
                del json_dict[j_key]['channel_id'] 
            if 'glitch_class_id' in json_dict[j_key]:
                cls_id = json_dict[j_key]['glitch_class_id']
                if cls_id is not None:
                    newquery = "select * from monitor_glitchclass where id={}".format(cls_id)
                    cursorObject.execute(newquery)
                    cls_rows = cursorObject.fetchall() 
                    json_dict[j_key]['class'] = {'name':cls_rows[0]['name'],
                                                 'description':cls_rows[0]['description'] }                            
                del json_dict[j_key]['glitch_class_id'] 
            if "glitch_pipeline_id" in json_dict[j_key]:
                pil_id = json_dict[j_key]["glitch_pipeline_id"]
                newquery = "select * from monitor_pipeline where id={}".format(pil_id)
                cursorObject.execute(newquery)
                pil_rows = cursorObject.fetchall() 
                json_dict[j_key]['pipeline'] = {'name':pil_rows[0]['name'],
                                                'description':pil_rows[0]['description'],
                                                'uri': '_',
                                                'command_line_args': pil_rows[0]['run_command'],
                                                'gps_runtime':"_"}                            
                del json_dict[j_key]["glitch_pipeline_id"] 
            j_key+=1                         

    except ValueError as e:
        print("Exeception occured:{}".format(e))
        return None

    finally:
        connectionObject.close()
        #print('CONNECTION CLOSE) 
    return json_dict     
    
if __name__=='__main__':
    
    gps_min = 1182000300
    gps_max = 1182000900
    snr_thr = 8
    dict_response = query_from_api_db(queryset='peak_time_gps>={} and peak_time_gps<={} and snr>={}'.format(gps_min, 
                                                                                                  gps_max, snr_thr))
    print(dict_response)
       
