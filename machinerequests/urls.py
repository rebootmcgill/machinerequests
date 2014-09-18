from django.conf.urls import patterns, url
from machinerequests.views import UnfilledRequestsList, ArchivedRequestsList, RequestView

urlpatterns = patterns('',
    # Examples:
    url(r'^$', UnfilledRequestsList.as_view(), 'Unfilled-Requests'),
    url(r'^archive/$', ArchivedRequestsList.as_view(), 'Archived-Requests'),
    url(r'^request/(?P<id>\d+)/$', RequestView.as_view(), 'Request-Details'),
    url(r'^machine/(?P<id>\d+)/$', MachineView.as_view(), 'Machine-Details'),
    # url(r'^blog/', include('blog.urls')),
)
