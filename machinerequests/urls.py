from django.conf.urls import patterns, url
from machinerequests.views import UnfilledRequestsList, ArchivedRequestsList, RequestView, MachineView

urlpatterns = patterns('',
    url(r'^$', UnfilledRequestsList.as_view()),
    url(r'^archive/$', ArchivedRequestsList.as_view()),
    url(r'^request/(?P<pk>\d+)/$', RequestView.as_view()),
    url(r'^request/(?P<machinerequest>\d+)/fulfill/$', RequestView.as_view()),
    url(r'^machine/(?P<pk>\d+)/$', MachineView.as_view()),
)
