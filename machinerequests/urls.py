from django.conf.urls import patterns, url
from machinerequests.views import UnfilledRequestsList, ArchivedRequestsList, RequestView, MachineView, MachineCreate

urlpatterns = patterns('machinerequests.views',
    url(r'^$', UnfilledRequestsList.as_view()),
    url(r'^archive/$', ArchivedRequestsList.as_view()),
    url(r'^request/(?P<pk>\d+)/$', RequestView.as_view(), name="Request-Details"),
    url(r'^request/(?P<machinerequest>\d+)/fulfill/$', MachineCreate.as_view()),
    url(r'^machine/(?P<pk>\d+)/$', MachineView.as_view(), name="Machine-Details"),
    url(r'^machine/(?P<pk>\d+)/pdf/$', 'generate_receipt', name="Machine-Receipt"),
)
