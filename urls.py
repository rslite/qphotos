from django.conf.urls.defaults import *
from django.contrib import admin
from qphotos.main import views

admin.autodiscover()

urlpatterns = patterns('',
	# Main page of the app
    (r'^$', views.index),

	# Used to import new media into the app
	(r'^browse$', views.browse),
	(r'^slide$', views.slide),
	(r'^import$', views.qimport),
	(r'^getfile$', views.getfile),
	(r'^deleteall$', views.deleteall),
	(r'^command$', views.command),

	(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),
	(r'^data/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'data'}),

    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
	
    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
