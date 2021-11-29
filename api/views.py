from django.shortcuts import render
from django.http import JsonResponse
from connect_to_mysql import query_from_api_db
from django.conf import settings
from monutils import get_run
 
if 'staging' in str(settings):  
    host_ = "ep-dev.ego-gw.eu"
if 'local' in str(settings):
    host_ = "127.0.0.1:8000"       

def index(request):
    return JsonResponse({"Hello, here you can make your glitch request":
                         {"View all O3a Virgo glitches":'http://{}/api/glitches'.format(host_),
                          "See documentation for selection use-cases":'http://{}/api/apidocs'.format(host_)}})
                          
def documentation(request):
    return JsonResponse({"This is the documentation page containing the correct API requests for glitches":
                         {"First select API from the domain":'/api',
                          "Select glitches from main Virgo channel, getting GPS-MIN, GPS-MAX, SNR-THRESHOLD":\
                          '/api/glitches/?gps-min=GPS-MIN&gps-max=GPS-MAX&snr-thr=SNR-THRESHOLD',
                          "Select glitches from single channel, getting CHANNEL-NAME, GPS-MIN, GPS-MAX, SNR-THRESHOLD":\
                          '/api/glitches/?channel=CHANNEL-NAME&gps-min=GPS-MIN&gps-max=GPS-MAX&snr-thr=SNR-THRESHOLD'}})                          
    
def get_glitches_in_json(request):
    gps_min = 1238612018
    gps_max = 1238612518
    snr_thr = 3
    ch_name = 'Hrec_hoft_16384Hz'
    if 'gps-min' in request.GET:
        gps_min = request.GET['gps-min']
    if 'gps-max' in request.GET:
        gps_max = request.GET['gps-max'] 
    if 'snr-thr' in request.GET:
        snr_thr = request.GET['snr-thr']
    if 'channel' in request.GET:
        ch_name = request.GET['channel']                
    
    obs_run = get_run(float(gps_min), float(gps_max))    
    data = query_from_api_db(channel_n=ch_name, run=obs_run,
                     queryset='peak_time_gps>={} and peak_time_gps<={} and snr>={}'.format(gps_min, 
                                                                           gps_max, snr_thr))     
    return JsonResponse(data)  
