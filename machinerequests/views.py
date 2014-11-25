import os

from django.views.generic import ListView, DetailView, CreateView
from machinerequests.models import Request, Machine
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse
#from django.contrib.staticfiles import finders
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import RequestContext
from django.conf import settings
from django.utils import timezone
from datetime import datetime
from machinerequests.functions import generate_reciept_pdf


# Create your views here.

def reboot_home(request):
    ops_phone = settings.OPS_PHONE
    now = timezone.now()
    month = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
    unfilled_count = Request.objects.filter(filled=False).count()
    pending_pickup_count = Machine.objects.filter(picked_up=False).count()
    orders_count = Request.objects.filter(requested_at__gte=month).count()
    filled_count = Request.objects.filter(filled=True, filled_at__gte=month).count()
    pickup_count = Machine.objects.filter(picked_up=True, pickedup_at__gte=month).count()
    orders_count_ever = Request.objects.count()
    filled_count_ever = Request.objects.filter(filled=True).count()
    pickup_count_ever = Machine.objects.filter(picked_up=True).count()
    return render_to_response('machine_requests/home.html',
        {'unfilled_count': unfilled_count, 'pending_pickup_count': pending_pickup_count, 'orders_count': orders_count,
            'filled_count': filled_count, 'pickup_count': pickup_count, 'orders_count_ever': orders_count_ever,
            'filled_count_ever': filled_count_ever, 'pickup_count_ever': pickup_count_ever,
            'ops_phone': ops_phone},
        context_instance=RequestContext(request))


class UnfilledRequestsList(ListView):
    context_object_name = 'request_list'
    queryset = Request.objects.filter(filled=False).order_by('requested_at')
    template_name = 'machine_requests/requests.html'

    def get_context_data(self, **kwargs):
        context = super(UnfilledRequestsList, self).get_context_data(**kwargs)
        context['page_title'] = "Unfulfilled Requests"
        return context


class ArchivedRequestsList(ListView):
    context_object_name = 'request_list'
    queryset = Request.objects.filter(filled=True).order_by('-filled_at')
    template_name = 'machine_requests/requests.html'

    def get_context_data(self, **kwargs):
        context = super(ArchivedRequestsList, self).get_context_data(**kwargs)
        context['page_title'] = "Request Archives"
        return context


class RequestView(DetailView):
    model = Request
    context_object_name = 'machinerequest'
    template_name = 'machine_requests/request_view.html'


class MachineCreate(CreateView):
    model = Machine
    fields = ['cpu', 'ram', 'hdd', 'notes']
    template_name = 'machine_requests/machine_create.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MachineCreate, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.request_id = self.kwargs['machinerequest']
        form.instance.fulfiller = self.request.user
        return super(MachineCreate, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(MachineCreate, self).get_context_data(**kwargs)
        context['machinerequest'] = Request.objects.get(pk=self.kwargs['machinerequest'])
        return context


class MachineView(DetailView):
    model = Machine
    context_object_name = 'machine'
    template_name = 'machine_requests/machine_view.html'


def mark_request_fulfilled(request, pk):
    req = get_object_or_404(Request, pk=pk)
    req.fulfill()
    return redirect(req)


def mark_machine_picked_up(request, pk):
    machine = get_object_or_404(Machine, pk=pk)
    machine.pickup()
    return redirect(machine)


def link_callback(uri, rel):
    # use short variable names
    sUrl = settings.STATIC_URL      # Typically /static/
    sRoot = settings.STATIC_ROOT    # Typically /home/userX/project_static/
    mUrl = settings.MEDIA_URL       # Typically /static/media/
    mRoot = settings.MEDIA_ROOT     # Typically /home/userX/project_static/media/

    # convert URIs to absolute system paths
    if uri.startswith(mUrl):
        path = os.path.join(mRoot, uri.replace(mUrl, ""))
    elif uri.startswith(sUrl):
        path = os.path.join(sRoot, uri.replace(sUrl, ""))

    # make sure that file exists
    if not os.path.isfile(path):
            raise Exception(
                    'media URI must start with %s or %s' %
                    (sUrl, mUrl))
    return path


def generate_receipt(request, pk):
    response = HttpResponse(content_type='application/pdf')
    machine = get_object_or_404(Machine, pk=pk)
    response['Content-Disposition'] = 'filename="machine-' + str(machine.id) + '.pdf"'
    pdf = generate_reciept_pdf(machine)
    response.write(pdf)
    return response