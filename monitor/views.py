from django.shortcuts import render
from django.db.models import Q, Max
from django.http import FileResponse
from django.conf import settings
import numpy as np
import pandas as pd
import csv
import os
import json
import time
import monutils
#db connection
from vini_db_connection import DBload

#bokeh
from bokeh.plotting import figure
from bokeh.layouts import column, layout, row
from bokeh.models import ColorBar, LinearColorMapper
from bokeh.models import ColumnDataSource, Div, Select
from bokeh.models.tickers import FixedTicker
from bokeh.palettes import Viridis256, Category10, Colorblind8
from bokeh.embed import components
from bokeh.models.callbacks import CustomJS

#add the hover
from bokeh.models import TapTool, OpenURL, HoverTool

from .models import GlitchInstance,GlitchClass,Channel,Pipeline

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import generic

#add gwdama
from gwdama.io import GwDataManager
#add time utilities 
from gwpy.time import from_gps, to_gps
# connection to database
from django.db import connections

base_conf_dir = ''
for i in os.getenv('PATH').split(':'):
    if i.endswith('virgo_glitches') or i.endswith('vini'):
            base_conf_dir=i

if 'staging' in str(settings): 
    base_conf_dir = "/var/www/html/reinforce/virgo_glitches" 

with open(os.path.join(base_conf_dir, 'data', 'config_monitor.json')) as f:
    monitor_parameters_dict = json.load(f)

def index(request, debug=False):
    """
    View function for home page of site.
    """
    if debug:
        import time
        start_time_proc = time.time()
        db_k=request
        r_mode = 'offline'
    if not debug:
        request.session['run'] = monutils.O3b_key
        db_k = request.session['run']
        request.session['mode'] = 'offline'
        r_mode = request.session['mode']
    
    #plot
    #get the data
    snr_min_list = 20
    if db_k=='default':
        home_conn = DBload('local')
    else:
        home_conn = DBload(db_k)
    #detector_id_value = home_conn.get_detector_id('V1')
    #channel_id_value = home_conn.get_channel_id(detector_id_value, 
    #                                            'Hrec_hoft_16384Hz')
    if r_mode=='online':
        dt_plot = 86400.
        now_gps = float(to_gps(datetime.datetime.now()))
        
        glitch_df = home_conn.get_glitches(now_gps-dt_plot, snr_min=snr_min_list,  
                                           channel_name='V1:Hrec_hoft_16384Hz')
        tmin_gps_plot = now_gps-dt_plot
        
    if r_mode=='offline':
        #gps_random = np.random.uniform(monutils.O3b_START, monutils.O3b_END) 
        tmin_gps_plot = [monutils.O3b_END-43200., monutils.O3b_END] 
        if 'local' in str(settings):
            tmin_gps_plot = [1185667218, 1185667218+1000.]
            
        glitch_df = home_conn.get_glitches(tmin_gps_plot[0], tmin_gps_plot[1],
                                           snr_min=snr_min_list,  
                                           channel_name='V1:Hrec_hoft_16384Hz') 
        tmin_gps_plot = tmin_gps_plot[0]
 
    if debug:
        end_time_proc = time.time()
        delta_time_proc = end_time_proc - start_time_proc
        print("The all glitches function takes {} seconds.".format(delta_time_proc))                     

    #convert the glitch list and plot it
    for conn in connections.all():
        conn.close()

    glitch_df_list = glitch_df
    if debug:
        end_time_proc = time.time()
        delta_time_proc = end_time_proc - start_time_proc
        print("1st Data Frame functions take {} seconds.".format(delta_time_proc))

    glitch_df.id = glitch_df.id.apply(str)

    if debug:
        end_time_proc = time.time()
        delta_time_proc = end_time_proc - start_time_proc
        print("Last Data Frame functions take {} seconds.".format(delta_time_proc))  

    # append the normalize SNR
    circle_max_size = 15
    circle_min_size = 5

    glitch_df_snr = glitch_df["snr"]
    snr_std = (glitch_df_snr - glitch_df_snr.min(axis=0)) / (glitch_df_snr.max(axis=0) - glitch_df_snr.min(axis=0))
    snr_std_range = snr_std * (circle_max_size - circle_min_size) + circle_min_size

    if debug:
        end_time_proc = time.time()
        delta_time_proc = end_time_proc - start_time_proc
        print("1st df functions take {} seconds.".format(delta_time_proc))  

    snr_df = pd.DataFrame({"SNR_rescaled": snr_std_range})

    if debug:
        end_time_proc = time.time()
        delta_time_proc = end_time_proc - start_time_proc
        print("2nd df functions take {} seconds.".format(delta_time_proc))  

    glitch_df = pd.concat([glitch_df, snr_df], axis=1)
    glitch_df['peak_time_gps_real'] = glitch_df['peak_time_gps'].astype(int)
    glitch_df['peak_time_gps'] = glitch_df['peak_time_gps']-tmin_gps_plot 

    if debug:
        end_time_proc = time.time()
        delta_time_proc = end_time_proc - start_time_proc
        print("Final df functions take {} seconds.".format(delta_time_proc))      

    hover = HoverTool(
        tooltips=[
            ("Time", "@peak_time_gps_real GPS"),
            ("Frequency","@peak_frequency Hz"),
            ("SNR", "@snr"),
            ("Click","View the glitch")
        ]
    )

    #create the plot
    glitch_time_plot = figure(plot_width=700, plot_height=400, 
                       tools=["reset", "box_zoom", hover, "tap"], 
                       y_axis_type="log", toolbar_location='below')

    # change just some things about the x-grid
    glitch_time_plot.xgrid.grid_line_color = None
    glitch_time_plot.ygrid.grid_line_color = "grey"

    # change just some things about the y-grid
    glitch_time_plot.ygrid.grid_line_alpha = 0.3
    glitch_time_plot.ygrid.grid_line_dash = [6, 4]

    glitch_time_plot.xaxis.axis_label = 'Time from {:.3f} GPS (s)'.format(tmin_gps_plot)
    glitch_time_plot.yaxis.axis_label = 'Frequency (Hz)'

    # Map the SNR to colors
    color_mapper = LinearColorMapper(palette=Viridis256, low=glitch_df["snr"].min(axis=0),
                                     high=glitch_df["snr"].max(axis=0))
    color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12, location=(0, 0), title='snr')

    # add a circle renderer with a size, color, and alpha
    glitch_time_plot.circle("peak_time_gps", "peak_frequency", color={'field': "snr", 'transform': color_mapper}, 
                            size={"field": "SNR_rescaled"}, alpha=0.6, source=glitch_df)

    if 'local' in str(settings): 
        url = "http://127.0.0.1:8000/monitor/glitch/@id"
    if 'staging' in str(settings): 
        url = "http://ep-dev.ego-gw.eu/monitor/glitch/@id"    
    taptool = glitch_time_plot.select(type=TapTool)
    taptool.callback = OpenURL(url=url)

    glitch_time_plot.add_layout(color_bar, 'right')
    
    #Store components
    script, div = components(glitch_time_plot)

    #prepare pagination and list
    #glitches_to_list = all_glitch_instances.filter(Q(snr__gte=snr_min_list)).order_by("-peak_time_gps")
    #glitches_to_list = glitches_to_plot.order_by("-peak_time_gps")

    if debug:
        end_time_proc = time.time()
        delta_time_proc = end_time_proc - start_time_proc
        print("The plot takes {} seconds.".format(delta_time_proc))
        page=1
               
#    if not debug:
#        page = request.GET.get('page', 1)
#    paginator = Paginator(all_glitch_instances, 20)
#
#    try:
#        glitches_to_list_paginated = paginator.page(page)
#    except PageNotAnInteger:
#        glitches_to_list_paginated = paginator.page(1)
#    except EmptyPage:
#        glitches_to_list_paginated = paginator.page(paginator.num_pages)

    # Render the HTML template monitor.index.html with the data in the context variable
    if debug:
        end_time_proc = time.time()
        delta_time_proc = end_time_proc - start_time_proc
        print("The paginator takes {} seconds.".format(delta_time_proc))
        return request
        
    del home_conn
    
    return render(
        request,
        'monitor/index.html',
        context={"run_k":db_k,
                 "glitches_to_list":glitch_df_list.iterrows(),
                 'the_script': script, 'the_div': div}
                 )
              
class ChannelListView(generic.ListView):
    queryset = Channel.objects.using(monutils.O3b_key).all()
    
    def get_queryset(self):
        db_k = self.request.session["run"]
        queryset = Channel.objects.using(db_k).all()
        return queryset
        
def glitchinstance_list(request): 
    m_lookback=0
    # Get context
    context = {}
    context['tmin_local']=""
    now = datetime.datetime.now()
    context['t_now_gps'] = time.mktime(now.timetuple()) - monutils.UTC_GPS_DIFFERENCE_SEC

    if "tmin_gps" in request.GET:
        context["m_tmin_gps"] = request.GET["tmin_gps"]
    else:
        context["m_tmin_gps"] = monutils.O3b_START

    if "tmax_gps" in request.GET:
        context["m_tmax_gps"] = request.GET["tmax_gps"]
    else:
        context["m_tmax_gps"] = monutils.O3b_END
    
    if float(context["m_tmin_gps"]) > monutils.O3b_END:  
        request.session['run'] = monutils.O3b_key
    else:
        request.session['run'] = monutils.get_run(float(context["m_tmin_gps"]), float(context["m_tmax_gps"]))
    db_k = request.session['run']           
            
    context["m_duration"] = str(float(context["m_tmax_gps"]) - float(context["m_tmin_gps"])) 

    if "fmin" in request.GET:
        context["m_fmin"] = request.GET["fmin"]
    else:
        context["m_fmin"] = 12

    if "fmax" in request.GET:
        context["m_fmax"] = request.GET["fmax"]
    else:
        context["m_fmax"] = 4096

    if "snrmin" in request.GET:
        context["m_snrmin"] = request.GET["snrmin"]
    else:
        context["m_snrmin"] = 0

    if "snrmax" in request.GET:
        context["m_snrmax"] = request.GET["snrmax"]
    else:
        context["m_snrmax"] = 1000

    context["run_k"] = db_k   

    #return context
    context["m_search_channel"] = None
    context["m_search_class"] = None
    context["m_search_pipeline"] = None
    if not "search_channel[]" in request.GET:
        context["search_channel[]"] = "Hrec_hoft_16384Hz"
    else:
        context["search_channel[]"] = request.GET["search_channel[]"]
    try:    
        context["m_search_channel"] = dict(request.GET.lists())["search_channel[]"]
        context["m_search_class"] = dict(request.GET.lists())["search_class[]"]
        context["m_search_pipeline"] = dict(request.GET.lists())["search_pipeline[]"]
    except KeyError:
        pass         

    # if lookback is specified
    if "lookback" in request.GET:
        now = datetime.datetime.now()
        tmin_gps = time.mktime(now.timetuple())-monutils.UTC_GPS_DIFFERENCE_SEC-float(request.GET["lookback"])
        tmin_unix = time.mktime(now.timetuple())-float(request.GET["lookback"])
        tmin_local = datetime.datetime.fromtimestamp(int(tmin_unix)).strftime('%Y-%m-%d %H:%M:%S')
        context['m_tmin_gps']=tmin_gps
        context['m_tmax_gps']=time.mktime(now.timetuple())-monutils.UTC_GPS_DIFFERENCE_SEC
        context['tmin_local'] = tmin_local 
        context["m_search_channel"] = ["V1:Hrec_hoft_16384Hz"]       
    
    # Get glitches list    
    if db_k=='default':
        list_conn = DBload('local')
    else:
        list_conn = DBload(db_k)   
        
    glitches_df = list_conn.get_glitches(gps_min=context['m_tmin_gps'], 
                                         gps_max=context['m_tmax_gps'], 
                                         frequency_min=context["m_fmin"],  
                                         frequency_max=context["m_fmax"], 
                                         snr_min=context["m_snrmin"], 
                                         snr_max=context["m_snrmax"],  
                                         channel_name=context["m_search_channel"], 
                                         pipeline_name=context["m_search_pipeline"], 
                                         class_name=context["m_search_class"])             
    
    del list_conn

    if glitches_df.empty:
        context['glitches_list'] = None
    else:
        context['glitches_list'] = glitches_df.iterrows()
           
    return render(request,
                  'monitor/glitchinstance_list.html',
                  context=context
                  )           
      
class GlitchInstanceDetailView(generic.DetailView):
    queryset = GlitchInstance.objects.using(monutils.O3b_key).all()

    def get_context_data(self, **kwargs):
        context = super(GlitchInstanceDetailView, self).get_context_data(**kwargs)
        db_k = self.request.session['run']
        context["run_k"] = db_k
        context["glitch_time_int"]=int(round(GlitchInstance.objects.using(db_k).get(pk=self.kwargs['pk']).peak_time_gps))
        context["glitch_time_min"]=float(GlitchInstance.objects.using(db_k).get(pk=self.kwargs['pk']).peak_time_gps)-1
        context["glitch_time_max"]=float(GlitchInstance.objects.using(db_k).get(pk=self.kwargs['pk']).peak_time_gps)+1
        glitch_time_date=from_gps(float(GlitchInstance.objects.using(db_k).get(pk=self.kwargs['pk']).peak_time_gps))
        try:
            glitch_time_date, gl_mus = str(glitch_time_date).split('.')
        except ValueError:
            print('No microsecond precision with this pipeline!!!')    
        context["glitch_time_date"] = str(glitch_time_date) # no microseconds
        return context

    def get_object(self):
        db_k = self.request.session['run']
        return GlitchInstance.objects.using(db_k).get(pk=self.kwargs['pk'])
        
    def get_queryset(self): 
        db_k = self.request.session['run'] 
        queryset = GlitchInstance.objects.using(db_k).all() 
        return queryset

class GlitchStatisticsDetailView(generic.DetailView):
    template_name = "monitor/glitchstatistics_detail.html"
    #queryset = GlitchInstance.objects.using(monutils.O3b_key).all()

    def get_context_data(self, **kwargs):
        context = super(GlitchStatisticsDetailView, self).get_context_data(**kwargs)
        db_k = self.request.session['run']
        if db_k=='default':
            stat_conn = DBload('local')
        else:
            stat_conn = DBload(db_k)        
        context["run_k"] = db_k
        context["total_glitches"] = stat_conn.count_glitches()
        context["total_glitches20"] = stat_conn.count_glitches("WHERE snr >= 20")       
        context["detector_channels"] = Channel.objects.using(db_k).all().count()
        context["detector_pipelines"] = Pipeline.objects.using(db_k).all().count()
        del stat_conn
        return context

    def get_object(self):
        db_k = self.request.session['run']
        return db_k    
        
class GlitchSearchView(generic.ListView):
    template_name = "monitor/glitch_search.html"
    queryset = Channel.objects.using(monutils.O3b_key).all() | Channel.objects.using(monutils.O3a_key).all() | Channel.objects.using(monutils.O2_key).all()

    def get_context_data(self, **kwargs):
        context = super(GlitchSearchView, self).get_context_data(**kwargs)

        list_available_glitch_classes = GlitchClass.objects.using(monutils.O3b_key).all()
        list_available_pipelines = Pipeline.objects.using(monutils.O3b_key).all()

        now = datetime.datetime.now()

        #default values for the form
        context["run_k"] = self.request.session['run']
        context['t_now_gps'] = time.mktime(now.timetuple()) - monutils.UTC_GPS_DIFFERENCE_SEC
        context["tmin_gps_default"] = monutils.O3b_START

        context["fmin_default"] = monitor_parameters_dict["SEARCH_PARAMETERS_DEFAULT"]["FREQUENCY"]["MIN"]
        context["fmax_default"] = monitor_parameters_dict["SEARCH_PARAMETERS_DEFAULT"]["FREQUENCY"]["MAX"]

        context["snrmin_default"] = monitor_parameters_dict["SEARCH_PARAMETERS_DEFAULT"]["SNR"]["MIN"]
        context["snrmax_default"] = monitor_parameters_dict["SEARCH_PARAMETERS_DEFAULT"]["SNR"]["MAX"]

        context["list_available_glitch_classes"] = list_available_glitch_classes
        
        m_classes_check_command = ' '
        m_classes_uncheck_command = ' '
        for cl in list_available_glitch_classes:
            m_classes_check_command += "document.getElementById('{}').checked = true; ".format(cl.name)
            m_classes_uncheck_command += "document.getElementById('{}').checked = false; ".format(cl.name)
        m_classes_check_command += "document.getElementById('NONE').checked = true; "
        m_classes_uncheck_command += "document.getElementById('NONE').checked = false; "     
        
        context["classes_check_command"] = m_classes_check_command
        context["classes_uncheck_command"] = m_classes_uncheck_command

        complex_channels = Channel.objects.using(monutils.O3b_key).all() | Channel.objects.using(monutils.O3a_key).all() | Channel.objects.using(monutils.O2_key).all()
        m_channels_check_command = ' '
        m_channels_uncheck_command = ' '
        for ch in complex_channels:
            m_channels_check_command += "document.getElementById('{}:{}').checked = true; ".format(ch.detector.code, ch.name)
            m_channels_uncheck_command += "document.getElementById('{}:{}').checked = false; ".format(ch.detector.code, ch.name) 
        
        context["channels_check_command"] = m_channels_check_command
        context["channels_uncheck_command"] = m_channels_uncheck_command
        
        context["list_available_pipelines"] = list_available_pipelines
        m_pipelines_check_command = ' '
        m_pipelines_uncheck_command = ' '
        
        for pl in list_available_pipelines:
            m_pipelines_check_command += "document.getElementById('{}').checked = true; ".format(pl.name)
            m_pipelines_uncheck_command += "document.getElementById('{}').checked = false; ".format(pl.name)
                    
        context["pipelines_check_command"] = m_pipelines_check_command
        context["pipelines_uncheck_command"] = m_pipelines_uncheck_command

        context["search_mode"] = self.kwargs["mode"][:1].upper()+self.kwargs["mode"][1:]

        return context 

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
import datetime

from .forms import LabelGlitchInstanceForm
from django.views.decorators.csrf import csrf_exempt 
from .models import OutputDirectory, Channel
from django.contrib.auth.models import User

@csrf_exempt
def label_glitch(request, id):
    glitch_inst=get_object_or_404(GlitchInstance, id = id)
    channel_inst = get_object_or_404(Channel,id=glitch_inst.channel_id)

    num_channels = Channel.objects.all().count()
    num_glitches=GlitchInstance.objects.all().count()
    num_glitch_classes=GlitchClass.objects.all().count()

    if request.method == 'GET':
        m_tmin_gps=None
        m_tmax_gps=None
        m_fmin=10
        m_fmax=1500
        m_snrmin=7
        m_snrmax=2000

    all_glitch_classes = GlitchClass.objects.all()

    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = LabelGlitchInstanceForm(data=request.POST)
        
        try:
            m_tmin_gps = request.POST["tmin_gps"]
            m_tmax_gps = request.POST["tmax_gps"]
        except KeyError:    
            m_tmin_gps=None
            m_tmax_gps=None
        
        try:        
            m_fmin = request.POST["fmin"]
            m_fmax = request.POST["fmax"]
            m_snrmin = request.POST["snrmin"]
            m_snrmax = request.POST["snrmax"]
        except KeyError:
            m_fmin=10
            m_fmax=1500
            m_snrmin=7
            m_snrmax=2000    

        #do it without checking for now..
        #glitch_inst.notes = form.cleaned_data['new_notes']

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            #book_inst.due_back = form.cleaned_data['renewal_date']
            #book_inst.save()
            glitch_inst.notes = form.cleaned_data['new_notes']

            glitch_class_name = form.cleaned_data['new_glitch_class_name']

            glitch_labeler_username = form.cleaned_data['new_labeler_username']

            m_class = GlitchClass.objects.get(name=str(glitch_class_name))
            m_user = User.objects.get(username=str(glitch_labeler_username))
            #print("rrr",glitch_class_code)
            glitch_inst.glitch_class = m_class
            glitch_inst.labeler = m_user
            #print("ff",form.cleaned_data)
            #print("GET",request.GET)


            glitch_inst.save()

            # redirect to a new URL:
            #return HttpResponseRedirect(reverse('glitches',kwargs={"tmin_gps":form.cleaned_data["tmin_gps"]}))
            return HttpResponseRedirect(reverse('glitches')+\
                "?tmin_gps="+str(form.cleaned_data["tmin_gps"])+\
                "&tmax_gps="+str(form.cleaned_data["tmax_gps"])+\
                "&fmin=" + str(form.cleaned_data["fmin"])+\
                "&fmax=" + str(form.cleaned_data["fmax"])+ \
                "&snrmin=" + str(form.cleaned_data["snrmin"])+\
                "&snrmax=" + str(form.cleaned_data["snrmax"])+\
                "&search_channel[]=Hrec_hoft_16384Hz")

    else:
        print("not valid")
        proposed_notes = glitch_inst.notes
        form = LabelGlitchInstanceForm(initial={'new_notes': proposed_notes,})

    return render(request, 'monitor/label_glitch.html', {'form': form, 'glitchinst':glitch_inst, \
                                                         "num_channels":num_channels,"num_glitch_classes":num_glitch_classes,\
                                                         "num_glitch_classes":num_glitch_classes,\
                                                         'all_glitch_classes':all_glitch_classes,\
                                                         'glitch_inst':glitch_inst,\
                                                         "tmin_gps":m_tmin_gps, "tmax_gps":m_tmax_gps,\
                                                         "fmin":m_fmin, "fmax":m_fmax, "snrmin":m_snrmin,              
                                                         "snrmax":m_snrmax,                                              
                                                         })

#Gwpy timeseries
from gwpy.timeseries import TimeSeries
from bokeh.models import SaveTool

def plot_qscan(request):
    m_tmin_gps = float(request.GET["tmin_gps"])
    m_tmax_gps = float(request.GET["tmax_gps"])
    request.session['run'] = monutils.get_run(m_tmin_gps, m_tmax_gps)
    db_k = request.session['run']
    if db_k=='default':
        scan_conn = DBload('local')
    else:
        scan_conn = DBload(db_k)
    try:
        peak_gps_glitchs = float(request.GET["tgps_glitch"])
        m_gps_glitchs = scan_conn.get_glitches(peak_gps_glitchs, peak_gps_glitchs, 
                                               channel_name=request.GET["ifo"]+':'+request.GET["channel"])
        additional_err = "Data may have been archived!"
    except KeyError:
        m_fmin = float(request.GET["fmin"])
        m_fmax = float(request.GET["fmax"]) 
        m_snrmin = float(request.GET["snrmin"])
        m_snrmax = float(request.GET["snrmax"]) 
        m_gps_glitchs = scan_conn.get_glitches(m_tmin_gps, m_tmax_gps, frequency_min=m_fmin,  
                                               frequency_max=m_fmax, snr_min=m_snrmin, snr_max=m_snrmax)
        additional_err = "Auxiliary channels data may not be present!"
    del scan_conn
    m_q_min = float(request.GET["q-min"])
    m_q_max = float(request.GET["q-max"])
    m_f_min = float(request.GET["f-min"])
    m_f_max = float(request.GET["f-max"])
    m_tw = float(request.GET["t-window"])
    #ifo_n = 'V1'
    #channel_n = 'Hrec_hoft_16384Hz'
    
    layouts = []
    
    data_seconds = 30
    
    time_ref = list(m_gps_glitchs.peak_time_gps)[0]
    if m_gps_glitchs['channel__name'].str.contains('Hrec_hoft_16384Hz').any():
        time_ref = m_gps_glitchs[m_gps_glitchs['channel__name']=='Hrec_hoft_16384Hz']['peak_time_gps']
        time_ref.reset_index(drop=True, inplace=True)
        time_ref = time_ref[0]
    #print('aaaaa', time_ref) 
         
    # Drop duplicated channels:
    m_gps_glitchs.drop_duplicates(subset=['channel__name', 'channel__detector__code'], inplace=True)

    dama = GwDataManager('dj_manager')  
    if 'staging' in str(settings):
        run = monutils.get_run(time_ref - data_seconds, time_ref + data_seconds)
        if run == 'O2':
            gwf_path=f'/data/prod/hrec/O2/O2-V1Online/'
        if run == 'O3a':
            gwf_path=f'/data/prod/hrec/O3A/V1Online/' 
        if run == 'O3b':
            gwf_path='/data/rawdata/**/**/'                 
        channels_list = [m_gps_g.channel__detector__code+':'+m_gps_g.channel__name for index, m_gps_g in m_gps_glitchs.iterrows()]                         
        try:
            dama_data = dama.read_gwdata(start=time_ref - data_seconds, 
                              end=time_ref + data_seconds, return_output=True,
                              dts_key='glitch_ts', gwf_path=gwf_path, 
                              verbose=True, channels=channels_list, 
                              data_source='local', resample=4096)
        except Exception as e:
            return render(request, 'monitor/plot_bokeh.html', {"add_err":additional_err})

    for index, m_gps_g in m_gps_glitchs.iterrows():
        if 'staging' in str(settings):
            if len(channels_list)==1: 
                timeseries_data = dama_data.to_TimeSeries() 
            else:        
                glitch_dset = dama_data['{}:{}'.format(m_gps_g.channel__detector__code, 
                                                       m_gps_g.channel__name)]
                timeseries_data = glitch_dset.to_TimeSeries()  

        if 'local' in str(settings):
            import utilities.glitch_models as g_models
            t_arr = np.linspace(time_ref - data_seconds, 
                                time_ref + data_seconds, 
                                int(2*4096*data_seconds)) 
            signal_noise_c = g_models.white_noise(t_arr)
            if m_gps_g.glitch_class__name=='GWScatteredLight':
                signal_noise_c+=g_models.scatlight_model(t_arr, m_gps_g.peak_time_gps, 
                                                         m_gps_g.duration,
                                                         m_gps_g.peak_frequency, 
                                                         m_gps_g.snr)   
            if m_gps_g.glitch_class__name=='GWSinGauss':
                signal_noise_c+=g_models.singauss_model(t_arr, m_gps_g.peak_time_gps, 
                                                        m_gps_g.duration,
                                                        m_gps_g.peak_frequency, 
                                                        m_gps_g.snr)                                            
            timeseries_data = TimeSeries(signal_noise_c, 
                                         sample_rate = 4096, 
                                         t0 = time_ref - data_seconds)
            tdset = dama.create_dataset('random_tdataset', data=timeseries_data)
            tdset.attrs.create('t0', str(time_ref - data_seconds))
            tdset.attrs.create('unit', '')
            tdset.attrs.create('channel', m_gps_g.channel__detector__code+':'+m_gps_g.channel__name)
            tdset.attrs.create('sample_rate', str(4096))
            tdset.attrs.create('name', "{}:{}".format(m_gps_g.channel__detector__code,
                                                      m_gps_g.channel__name))
                                     
        qscan_data = timeseries_data.q_transform(qrange=(m_q_min, m_q_max), 
                                             frange=(m_f_min, m_f_max), logf=True,             
                                             gps=time_ref, whiten=True,   
                                             outseg=(time_ref - m_tw/2, 
                                                     time_ref + m_tw/2))
 
        q_f = qscan_data.frequencies.value
        q_t = qscan_data.times.value - time_ref
        Sxx = qscan_data.value                                
    
        TOOLS = ['box_zoom', 'reset', 'save']
             
        figdict = dict(plot_width=650, plot_height=400, toolbar_location='below',
                       background_fill_color=Viridis256[5],
                       title="Q-scan {}:{}".format(m_gps_g.channel__detector__code,
                                                   m_gps_g.channel__name),                                 
                       y_axis_type='log',
                       x_axis_label = 'Time from {} GPS [s]'.format(time_ref),
                       y_axis_label = 'Frequency [Hz]',
                       x_range=(- m_tw/2, m_tw/2),
                       y_range=(q_f[0], q_f[-1]),
                       tools=TOOLS)
    
        spectogram_figure = figure(**figdict)
        spectogram_figure.image(image=[Sxx.T],
                                x=[q_t[0]],
                                y=[q_f[0]],
                                dw=[q_t[-1] - q_t[0]],
                                dh=[q_f[-1] - q_f[0]], 
                                palette=Viridis256, level="image")
                                
        #spectogram_figure.xgrid.grid_line_color = None
        #spectogram_figure.ygrid.grid_line_color = None
        spectogram_figure.title.align = 'center'
    
        mapper = LinearColorMapper(palette=Viridis256, low=1, high=np.percentile(Sxx,99))
    
        color_bar = ColorBar(color_mapper=mapper, major_label_text_font_size='8pt',
                             title="             Norm En", title_text_align='center',
                             title_text_font_size='9pt', orientation='vertical', 
                             title_text_font_style='bold', 
                             label_standoff=6, location=(0, 0), border_line_color=None)  

        #color_bar_plot = figure(title="Normalised Energy", title_location="right", 
        #                        height=figdict['plot_height'], width=100, 
        #                        toolbar_location=None, min_border=0, 
        #                        outline_line_color=None)

        #color_bar_plot.add_layout(color_bar, 'right')
        #color_bar_plot.title.align="center"
        #color_bar_plot.title.text_font_size = '10pt'

        spectogram_figure.add_layout(color_bar, 'right')
        spectogram_figure.grid.grid_line_width = 0.25
        #layout = row(spectogram_figure, color_bar_plot)     
            
        #Store components
        #script, div = components(layout)
        layouts.append(spectogram_figure)
    dama.close()
    del dama
    #Feed them to the Django template.
    final_layout = column(*layouts) 
    script, div = components(final_layout)

    return render(request, 'monitor/plot_bokeh.html', {"run_k":db_k,
                                                       'the_script' : script, 
                                                       'the_div' : div,
                                                        })

@csrf_exempt
def plot_glitches(request, debug=False):
    """

    :param request:
    :return:
    """
    
    #parse variables from POST
    m_tmin_gps = request.POST["tmin_gps"]
    m_tmax_gps = request.POST["tmax_gps"]
    m_fmin = request.POST["fmin"]
    m_fmax = request.POST["fmax"]
    m_snrmin = request.POST["snrmin"]
    m_snrmax = request.POST["snrmax"]

    if float(m_tmin_gps) > monutils.O3b_END:  
        request.session['run'] = monutils.O3b_key
    else:
        request.session['run'] = monutils.get_run(float(m_tmin_gps), float(m_tmax_gps))
    db_k = request.session['run'] 
    
    if db_k=='default':
        plot_conn = DBload('local')
    else:
        plot_conn = DBload(db_k)
    
    search_channel_list = None
    if "search_channel[]" in request.POST:  
        search_channel_list = request.POST.getlist("search_channel[]") 
        search_channel_list = list(map(str, search_channel_list)) 
    
    search_class_list = None    
    if "search_class[]" in request.POST:
        search_class_list = request.POST.getlist("search_class[]")
        search_class_list = list(map(str, search_class_list))
        
    search_pipeline_list = None    
    if "search_pipeline[]" in request.POST:
        search_pipeline_list = request.POST.getlist("search_pipeline[]")  
        search_pipeline_list = list(map(str, search_pipeline_list))      

    glitch_df = plot_conn.get_glitches(gps_min=m_tmin_gps, gps_max=m_tmax_gps, 
                                       frequency_min=m_fmin, frequency_max=m_fmax,
                                       snr_min=m_snrmin, snr_max=m_snrmax, 
                                       channel_name=search_channel_list, 
                                       pipeline_name=search_pipeline_list, 
                                       class_name=search_class_list)
    del plot_conn                                   
    if glitch_df.empty:
        return render(request, 'monitor/plot_glitches.html', {"run_k":db_k, "m_tmin_gps":m_tmin_gps,
                                                             "m_tmax_gps":m_tmax_gps,
                                                             "m_fmin":m_fmin,"m_fmax":m_fmax,
                                                             "m_snrmin":m_snrmin,"m_snrmax":m_snrmax})                                          
                                       
    # Get full channel name column (e.g. V1:..)                                                     
    def f(x):
        return x['channel__detector__code']+':'+x['channel__name']
    
    chans_values = list(set(list(glitch_df.apply(f, axis=1))))

    channel_column = pd.DataFrame(dict(channel=list(glitch_df.apply(f, axis=1))))
    if 'channel__name' in glitch_df:
        glitch_df.drop('channel__name', inplace=True, axis=1)   
    if 'channel__detector__code' in glitch_df:
        glitch_df.drop('channel__detector__code', inplace=True, axis=1)
    glitch_df = pd.concat([glitch_df, channel_column], axis=1)
    
    glitch_df.id = glitch_df.id.apply(str)

    # append the normalized SNR
    circle_max_size = 15
    circle_min_size = 5

    glitch_df_snr = glitch_df["snr"]
    snr_std = (glitch_df_snr - glitch_df_snr.min(axis=0)) / (glitch_df_snr.max(axis=0) - glitch_df_snr.min(axis=0))
    snr_std_range = snr_std * (circle_max_size - circle_min_size) + circle_min_size
    snr_df = pd.DataFrame({"snr_rescaled": snr_std_range})
    
    clsres_df = pd.DataFrame({'cls_rescaled': 5*np.ones(len(snr_std_range))})
    # What if the glitch doesn't belong to any class?
    # Rename it with a 'NONE' class
    glitch_df['glitch_class__name'].fillna(value='NONE', inplace=True)
    
    # Group minor classes with None_of_the_Above label
    counted_classes = glitch_df['glitch_class__name'].value_counts().to_dict()
    n_clss = len(counted_classes)
    if n_clss >= 10:
        last_cls = n_clss - 9
        minor_classes = list(counted_classes.keys())[-last_cls:]
        glitch_df['glitch_class__name_real'] = glitch_df['glitch_class__name']
        glitch_df['glitch_class__name'] = glitch_df.replace(minor_classes, 'None_of_the_Above')['glitch_class__name']

    # Create a data column that enumerate glitches classes            
    classes_values = list(set(list(glitch_df['glitch_class__name'])))
    classes_dict = {val:i for i, val in enumerate(classes_values)}
    # Order the dictionary in case of minor classes
    if n_clss >= 10:
        from operator import itemgetter
        from collections import OrderedDict
        # Keep None_of_the_above on the top of color bar
        i_cl_num = classes_dict['None_of_the_Above']
        last_d_el = list(classes_dict.items())[-1]
        classes_dict[last_d_el[0]] = i_cl_num
        classes_dict['None_of_the_Above'] = last_d_el[1]
        # Sort the dictionary
        sorted_cd = sorted(classes_dict.items(), key=itemgetter(1))
        classes_dict = OrderedDict(sorted_cd)
    # Create dataframe for classes enumeration   
    classes_df = pd.DataFrame({'cls_nums': [classes_dict[val] for val in glitch_df['glitch_class__name']]})

    # Concatenate all column to original dataframe
    glitch_df = pd.concat([glitch_df, classes_df, snr_df, clsres_df], axis=1)
  
    # Make a time offset, considering a value in the middle of the selected time interval.  
    tres_ = np.array([int(sub.split('.')[0]) for sub in np.array(glitch_df["peak_time_gps"]).astype(np.str)])
    gps_ref_time = int(tres_.mean())
    glitch_df["peak_time_gps_real"] = glitch_df["peak_time_gps"].astype(int)
    glitch_df["peak_time_gps"] = list(np.array(glitch_df["peak_time_gps"]) - gps_ref_time)

    axis_map = {
        "SNR": "snr",
        "GPS Time from {}".format(gps_ref_time): "peak_time_gps",
        "Frequency (Hz)": "peak_frequency",
        "Frequency bandwidth (Hz)": "bandwidth",
        "Duration (s)": "duration",
         }
         
    zaxis_map = {
        "SNR": ("snr", "snr_rescaled"),
        "CLASS": ("cls_nums", "cls_rescaled"),
        }

    xselect = "GPS Time from {}".format(gps_ref_time)
    yselect = "Frequency (Hz)"
    zselect = "SNR"

    # Create Input controls

    x_axis = Select(title="X Axis", options=sorted(axis_map.keys()), value=xselect)
    y_axis = Select(title="Y Axis", options=sorted(axis_map.keys()), value=yselect)
    z_axis = Select(title="Z Axis", options=sorted(zaxis_map.keys()), value=zselect)
    
    pipes_values = list(set(list(glitch_df['glitch_pipeline__name'])))
    pipes_values = ['All'] + pipes_values
    if 'V1:Hrec_hoft_16384Hz' in chans_values: 
        channel_val = 'V1:Hrec_hoft_16384Hz'
    else:
        channel_val = chans_values[0]
    channels_sl = Select(title="Channel", options=chans_values, value=channel_val)
    pipeline_val = "All"
    pipelines_sl = Select(title="Pipeline", options=pipes_values, value=pipeline_val)
  
    # Default x and y values on axis  
    plot_df = pd.DataFrame(glitch_df.loc[glitch_df['channel'] == channel_val])  
    glitch_df['x'] = plot_df[axis_map[xselect]]
    glitch_df['y'] = plot_df[axis_map[yselect]]
    glitch_df['z'] = plot_df[zaxis_map[zselect][0]]
    glitch_df['z_rescaled'] = plot_df[zaxis_map[zselect][1]]

    # Create Column Data Source that will be used by the plot
    source_view = {cv:ColumnDataSource(pd.DataFrame(glitch_df.loc[glitch_df['channel'] == cv])) for cv in chans_values}
    source_view = {'All':source_view}
    for pv in pipes_values[1:]:
        filtered_glitch_df = pd.DataFrame(glitch_df.loc[glitch_df['glitch_pipeline__name'] == pv])
        up_source_view = {pv:{cv:ColumnDataSource(pd.DataFrame(filtered_glitch_df.loc[glitch_df['channel'] == cv]))  for cv in chans_values}}
        source_view.update(up_source_view)
    source = ColumnDataSource(glitch_df)
    
    if n_clss >= 10:
        creal_label = 'glitch_class__name_real'
    else:
        creal_label = 'glitch_class__name'    
    hover = HoverTool(
            tooltips=[
                     ("Time", "@peak_time_gps_real GPS"),
                     ("Frequency","@peak_frequency Hz"),
                     ("SNR", "@snr"),
                     ("Label", "@{}".format(creal_label)),
                     ("Click","View the glitch")
                     ]
                     )

    #create the plot
    glitch_time_plot = figure(plot_width=700, plot_height=400, 
                          tools=["reset", "box_zoom", hover, "tap", "save"], 
                          y_axis_type="log", 
                          toolbar_location='above')

    ##################################################################################

    # create the histograms with updated values on the axis

    sourcedf = {}
    default_dicts = {} 
    for k in pipes_values:
        sourcedf[k] = {}
        for i in chans_values:
            sourcedf[k][i] = {}
            for j in list(axis_map.values()):
                x_data = source_view[k][i].data[j]
                x_values = x_data[np.logical_not(np.isnan(x_data))]
                hhist, hedges = np.histogram(x_values, bins=20)
                hzeros = np.zeros(len(hedges)-1)
                dict_hdata = dict(th=hhist, tz=hzeros, l=hedges[:-1], r=hedges[1:])
                sourcedf[k][i][j] = ColumnDataSource(dict_hdata)
                if k == pipeline_val and i == channel_val and j == axis_map[xselect]:
                    default_dicts['x'] = dict_hdata
                if k == pipeline_val and i == channel_val and j == axis_map[yselect]:
                    default_dicts['y'] = dict_hdata    
            
    # first histogram     
    sourceh = ColumnDataSource(default_dicts['x'])
    #hmax = max(sourceh.data['th'])*1.1

    LINE_ARGS = dict(color="#3A5785", line_color=None)

    ph = figure(toolbar_location='right', plot_width=glitch_time_plot.plot_width, plot_height=200, #x_range=glitch_time_plot.x_range, y_range=(0, hmax),
                min_border=10, min_border_left=50, y_axis_location="left", tools=['save'])
    ph.xgrid.grid_line_color = None

    hh2 = ph.quad(bottom=0, left='l', right='r', top='th', color="white", line_color="#3A5785", source=sourceh)
    hh2 = ph.quad(bottom=0, left='l', right='r', top='tz', alpha=0.5, **LINE_ARGS, source=sourceh)
    #hh2 = ph.quad(bottom=0, left='l', right='r', top='tz', alpha=0.1, **LINE_ARGS, source=sourceh)

    # second histogram   
    sourcev = ColumnDataSource(default_dicts['y'])
    #vmax = max(sourcev.data['th'])*1.1

    pv = figure(toolbar_location='right', plot_width=glitch_time_plot.plot_width, plot_height=200, #x_range=glitch_time_plot.y_range, y_range=(0, vmax), 
                min_border=10, min_border_left=50, y_axis_location="left", tools=['save'])
    pv.xgrid.grid_line_color = None

    vh1 = pv.quad(bottom=0, left='l', right='r', top='th', color="white", line_color="#3A5785", source=sourcev)
    vh2 = pv.quad(bottom=0, left='l', right='r', top='tz', alpha=0.5, **LINE_ARGS, source=sourcev)
    #vh2 = pv.quad(bottom=0, left='l', right='r', top='tz', alpha=0.1, **LINE_ARGS, source=sourcev)
    
    ph.xaxis.axis_label = xselect
    pv.xaxis.axis_label = yselect

    ##############################################################################

    # change just some things about the x-grid
    glitch_time_plot.xgrid.grid_line_color = None
    glitch_time_plot.ygrid.grid_line_color = "grey"

    # change just some things about the y-grid
    glitch_time_plot.ygrid.grid_line_alpha = 0.3
    glitch_time_plot.ygrid.grid_line_dash = [6, 4]

    glitch_time_plot.xaxis.axis_label = xselect
    glitch_time_plot.yaxis.axis_label = yselect

    # Map the SNR to colors
    color_mapper = LinearColorMapper(palette=Viridis256, low=source.data["snr"].min(axis=0),
                                     high=source.data["snr"].max(axis=0))
    color_bar = ColorBar(color_mapper=color_mapper, label_standoff=6, location=(0, 0), title='SNR')
    c_dict = {v: k for k, v in classes_dict.items()}
    snr_ticks = color_bar.ticker

    # add a circle renderer with a size, color, and alpha
    cir = glitch_time_plot.circle("x", "y", color={'field': "z", 'transform': color_mapper},
                 size={"field": "z_rescaled"}, alpha=0.6, source=source)
    glitch_time_plot.add_layout(color_bar, 'right') 

    if 'local' in str(settings):
        url = "http://127.0.0.1:8000/monitor/glitch/@id"
    if 'staging' in str(settings):    
        url = "http://ep-dev.ego-gw.eu/monitor/glitch/@id"
    
    taptool = glitch_time_plot.select(type=TapTool) 
    taptool.callback = OpenURL(url=url)

    category10 = list(Category10[10])
    category10[-1] = Colorblind8[-1]
    category10[-3] = Colorblind8[2]
    
    # Check the class with the higher number of letters
    classes_letts = [len(cv_c) for cv_c in list(classes_dict.keys())]
    proper_standoff = 2*max(classes_letts) 

    callback = CustomJS(args=dict(source=source, sourceh=sourceh, sourcev=sourcev, 
                        source_view=source_view, sourcedf=sourcedf, viridis256 = Viridis256, category10 = category10[:len(classes_values)],
                        select01=pipelines_sl, select02=channels_sl, select1=x_axis, select2=y_axis, select3=z_axis,
                        color_bar=color_bar, c_dict=c_dict, snr_ticks=snr_ticks, cir_plot = cir, p_standoff = proper_standoff,
                        hax1 = ph.xaxis, hax2 = pv.xaxis, c_ticks=FixedTicker(ticks=list(c_dict.keys())),
                        ax1=glitch_time_plot.xaxis, ax2=glitch_time_plot.yaxis, a_map=axis_map, za_map=zaxis_map), code="""
                        var pipeline_val = select01.value;
                        var channel_val = select02.value;  
                        var xselect = select1.value;
                        var yselect = select2.value;
                        var zselect = select3.value;
                        hax1[0].axis_label = xselect;
                        hax2[0].axis_label = yselect;                        
                        ax1[0].axis_label = xselect;
                        ax2[0].axis_label = yselect;
                        var vmin = Math.min.apply(Math, source_view[pipeline_val][channel_val].data[za_map[zselect][0]]);
                        var vmax = Math.max.apply(Math, source_view[pipeline_val][channel_val].data[za_map[zselect][0]]);   
                        color_bar.title = zselect;                         
                        if (zselect == 'CLASS') {
                            if (c_ticks.ticks.length == 1) { 
                                var vmin = -0.5;
                                var vmax = 0.5;
                            }
                            else { 
                                var vmin = c_ticks.ticks[0];
                                var vmax = c_ticks.ticks[c_ticks.ticks.length - 1];
                            }
                            color_bar.ticker = c_ticks;
                            color_bar.label_standoff = p_standoff;
                            color_bar.major_label_overrides = c_dict;                            
                            var color_mapper = new Bokeh.CategoricalColorMapper({palette:category10, factors:c_ticks.ticks});
                            cir_plot.color = {field:'z', transform:color_mapper};
                            color_bar.color_mapper.palette = category10;
                        }
                        else {
                            color_bar.ticker = snr_ticks;
                            color_bar.label_standoff = 6;                         
                            var color_mapper = new Bokeh.LinearColorMapper({palette:viridis256, low:vmin, high:vmax});
                            cir_plot.color = {field:'z', transform:color_mapper};
                            color_bar.color_mapper.palette = viridis256;                                                     
                        }
                        color_bar.color_mapper.low = vmin;
                        color_bar.color_mapper.high = vmax; 
                        source.data = source_view[pipeline_val][channel_val].data;
                        source.data['x'] = source.data[a_map[xselect]];
                        source.data['y'] = source.data[a_map[yselect]];
                        source.data['z'] = source.data[za_map[zselect][0]];
                        source.data['z_rescaled'] = source.data[za_map[zselect][1]];
                        var filt_source = sourcedf[pipeline_val][channel_val]; 
                        sourceh.data = filt_source[a_map[xselect]].data;
                        sourcev.data = filt_source[a_map[yselect]].data;
                        sourceh.change.emit();
                        source.change.emit();
                        sourcev.change.emit();
                        """)                   
    
    x_axis.js_on_change("value", callback)
    y_axis.js_on_change("value", callback)
    z_axis.js_on_change("value", callback)
    channels_sl.js_on_change("value", callback)
    pipelines_sl.js_on_change("value", callback)

    inputs1 = column(x_axis, y_axis, 
                    #width=320, height=1000,
                    )
    inputs2 = column(channels_sl, pipelines_sl,
                    #width=320, height=1000,
                    )                
    lay_ = layout([[inputs1, inputs2], [glitch_time_plot, z_axis],
                     [ph], [pv],
            ],  
            ) 

    interactive_plot_script, interactive_plot_div = components(lay_)

    return render(request, 'monitor/plot_glitches.html',\
                  {"run_k":db_k, "m_tmin_gps":m_tmin_gps,"m_tmax_gps":m_tmax_gps,
                   "m_fmin":m_fmin,"m_fmax":m_fmax,
                   "m_snrmin":m_snrmin,"m_snrmax":m_snrmax, 
                   'the_script': interactive_plot_script, 'the_div': interactive_plot_div})


def export_glitch_data(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="glitchlist.csv"'

    if "format" in request.GET:
        pass

    #process GET variables
    #time
    m_tmin_gps = monutils.O3b_START
    m_tmax_gps = monutils.O3b_END
    if ("tmin_gps" in request.GET) and len(request.GET["tmin_gps"])>0:
        m_tmin_gps = request.GET["tmin_gps"]
    if ("tmax_gps" in request.GET) and len(request.GET["tmax_gps"])>0:
        m_tmax_gps = request.GET["tmax_gps"]
        
    #get glitch data
    request.session["run"] = monutils.get_run(float(m_tmin_gps), 
                                              float(m_tmax_gps))
    db_k = request.session["run"]   

    #frequency
    m_fmin = 0.
    m_fmax = 1e5

    if ("fmin" in request.GET) and len(request.GET["fmin"])>0:
        m_fmin = float(request.GET["fmin"])
    if ("fmax" in request.GET) and len(request.GET["fmax"])>0:
        m_fmax = float(request.GET["fmax"])

    #SNR
    m_snr_min = 0.
    m_snr_max=1e6
    if "snrmin" in request.GET:
        m_snr_min = request.GET["snrmin"]
    if "snrmax" in request.GET:
        m_snr_max = request.GET["snrmax"]
    
    #CHANNELS 
    search_channel_list = None   
    if "search_channel[]" in request.GET:
        search_channel_list = request.GET.getlist("search_channel[]")
    
    #CLASSES               
    search_class_list = None
    if "search_class[]" in request.GET:
        search_class_list = request.GET.getlist("search_class[]") 
        
    #PIPELINE               
    search_pipeline_list = None
    if "search_pipeline[]" in request.GET:
        search_pipeline_list = request.GET.getlist("search_pipeline[]")                                

    #write HEADER
    header_var = ['peak_time_gps', 'duration','peak_frequency','bandwidth','snr','glitch_class']

    var_to_save = None
    if "download_column[]" in request.GET:
        var_to_save = request.GET.getlist("download_column[]")
    else:
        var_to_save = header_var
    
    if db_k=='default':
        exp_conn = DBload('local')
    else:
        exp_conn = DBload(db_k)
    
    glitches_to_save = exp_conn.get_glitches(gps_min=m_tmin_gps, gps_max=m_tmax_gps, 
                                             frequency_min=m_fmin, frequency_max=m_fmax,
                                             snr_min=m_snr_min, snr_max=m_snr_max, 
                                             channel_name=search_channel_list, 
                                             pipeline_name=search_pipeline_list, 
                                             class_name=search_class_list)                                                                                   
                                                                             
    # Prepare to the download
    glitches_to_save.rename(columns={'glitch_class__name':'glitch_class',
                                     'glitch_pipeline__name':'glitch_pipeline'}, inplace=True)
                                     
    glitches_to_save['glitch_class'].fillna(value='None', inplace=True)
    
    def f(x):
        return x['channel__detector__code']+':'+x['channel__name']
    
    chans_values = list(set(list(glitches_to_save.apply(f, axis=1))))

    channel_column = pd.DataFrame(dict(channel=list(glitches_to_save.apply(f, axis=1))))
    if 'channel__name' in glitches_to_save:
        glitches_to_save.drop('channel__name', inplace=True, axis=1)   
    if 'channel__detector__code' in glitches_to_save:
        glitches_to_save.drop('channel__detector__code', inplace=True, axis=1)
    glitches_to_save = pd.concat([glitches_to_save, channel_column], axis=1)
    
    # Select the desired columns
    glitches_to_save = glitches_to_save[var_to_save]
    
    # return a CSV file
    glitches_to_save.to_csv(path_or_buf=response)
             
    del exp_conn
    return response
    
def download_timeseries(request):
    db_k = request.session['run']
    m_tmin_gps = int(float(request.GET["tmin_gps"]))
    m_tmax_gps = int(float(request.GET["tmax_gps"]))
    m_gps_glitch = float(request.GET["tgps_glitch"])
    m_ifo = request.GET["ifo"]
    m_channel = request.GET["channel"]
    m_tobs = float(m_tmax_gps) - float(m_tmin_gps)
    
    file_path = os.path.join(base_conf_dir, 'data', 'gwdama_timeseries',
                            "{}_{}GPS.h5".format(m_tmin_gps, m_tmax_gps))
    if 'local' in str(settings): 
        import utilities.glitch_models as g_models
        dama = GwDataManager('test_manager')
        t_arr = np.linspace(m_tmin_gps, m_tmax_gps, int(m_tobs*4096)) 
        data_sim = g_models.white_noise(t_arr)
        #if m_gps_g.glitch_class.name=='GWScatteredLight':
        #    signal_noise_c+=g_models.scatlight_model(t_arr, m_gps_g.peak_time_gps, 
        #                                             m_gps_g.duration,
        #                                             m_gps_g.peak_frequency, 
        #                                             m_gps_g.snr)   
        #if m_gps_g.glitch_class.name=='GWSinGauss':
        #    signal_noise_c+=g_models.singauss_model(t_arr, m_gps_g.peak_time_gps, 
        #                                            m_gps_g.duration,
        #                                            m_gps_g.peak_frequency, 
        #                                            m_gps_g.snr)                           
        dama = GwDataManager('test_manager')
        dset = dama.create_dataset('random_dataset', data=data_sim)
        dset.attrs.create('t0', str(m_tmin_gps))
        dset.attrs.create('unit', '')
        dset.attrs.create('channel', m_channel)
        dset.attrs.create('sample_rate', str(4096))
        dset.attrs.create('name', "{}:{}".format(m_ifo, m_channel))
    if 'staging' in str(settings):
        run = monutils.get_run(m_tmin_gps, m_tmax_gps)
        if run == 'O2':
            gwf_path=f'/data/prod/hrec/O2/O2-V1Online/'
        if run == 'O3a':
            gwf_path=f'/data/prod/hrec/O3A/V1Online/' 
        if run == 'O3b':
            gwf_path='/data/rawdata/**/**/'                 
        dama = GwDataManager('dj_manager')                   
        try:
            dama.read_gwdata(start=m_tmin_gps, 
                             end=m_tmax_gps,
                             dts_key='glitch_ts', gwf_path=gwf_path,
                             verbose=True,
                             channels=m_ifo+':'+m_channel, 
                             data_source='local')
        except Exception as e:
            return render(request, 'monitor/plot_bokeh.html', {})   
    dama.write_gwdama(file_path) 
    response = FileResponse(open(file_path, 'rb')) 
    os.remove(file_path)  
    dama.close()
    del dama                            
    return response
                
