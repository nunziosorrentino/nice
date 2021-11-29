from django.conf.urls import url,include

from . import views
    
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^channels/$', views.ChannelListView.as_view(), name='channels'),
    #url(r'^glitches/$', views.GlitchInstanceListView.as_view(), name='glitches'),
    url(r'^glitches/$', views.glitchinstance_list, name='glitches'),
    url(r'^statistics/$', views.GlitchStatisticsDetailView.as_view(), name='statistics'),
    url(r'^glitch/(?P<pk>[\w\d-]+)$', views.GlitchInstanceDetailView.as_view(), name='glitchinstance-detail'),
    url(r'^search/(?P<mode>[\w\d-]+)$', views.GlitchSearchView.as_view(),name='search'),
    url(r'^plot/$', views.plot_glitches, name='plot'),
    url(r'^label/(?P<id>[\w\d-]+)$', views.label_glitch, name='label-glitch'),
    #url(r'^glitch/(?P<pk>[-\w]+)$', views.label_glitch, name='label-glitch'),
    url(r'^plot/glitch/$', views.plot_qscan, name='qbokeh'),
    #url(r'^plot/glitches/$', views.plot_multichans, name='qbokehs'),
    #url(r'^plot/$', views.plot_glitch, name='plot'),
    url(r'^export/glitch/$', views.export_glitch_data, name='export_data_csv'),
    url(r'^loaddama/glitch/$', views.download_timeseries, name='load_dama_hdf')
]

