from django.urls import path
from django.conf.urls import url,include

from . import views

urlpatterns = [
    url(r'^$', views.index, name='apiindex'),
    url(r'^glitches/$', views.get_glitches_in_json, name='apiglitches'),
    url(r'^apidocs/$', views.documentation, name='apidocumentation'),
]
