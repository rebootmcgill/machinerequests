import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
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


from io import BytesIO


# Create your views here.

def reboot_home(request):
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
            'filled_count_ever': filled_count_ever, 'pickup_count_ever': pickup_count_ever},
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
    response_buffer = BytesIO()
    p = canvas.Canvas(response_buffer, pagesize=letter)
    #p.drawImage(finders.find("img/logo.png"), 50, 50)
    p.setLineWidth(.3)
    p.setFont('Helvetica', 12)
    p.drawString(30, 750, 'OFFICIAL COMMUNIQUE')
    p.drawString(30, 735, 'OF REBOOT')
    p.drawString(500, 750, str(machine.request.filled_at.date()))
    p.line(480, 747, 580, 747)
    p.drawString(480, 725, 'ORDER #' + str(machine.request.id) + '-' + str(machine.id))
    p.line(465, 723, 555, 723)
    p.drawString(30, 703, 'ORDERED BY:')
    p.line(120, 700, 220, 700)
    p.drawString(130, 703, str(machine.request.full_name()))
    p.drawString(250, 703, 'FACULTY:')
    p.line(310, 700, 600, 700)
    p.drawString(320, 703, str(machine.request.faculty_and_dept))
    p.drawString(30, 675, 'FULFILLED BY:')
    p.line(120, 672, 320, 672)
    p.drawString(130, 675, str(machine.fulfiller.get_full_name()))
    p.drawString(30, 650, 'PERIPHERALS:')
    p.rect(50, 615, 550, 30)
    p.drawString(60, 625, 'DISPLAY:')
    p.rect(120, 620, 20, 20)
    if(machine.request.need_display):
        p.line(120, 620, 140, 640)
        p.line(140, 620, 120, 640)
    p.drawString(160, 625, 'MOUSE:')
    p.rect(210, 620, 20, 20)
    if(machine.request.need_mouse):
        p.line(210, 620, 230, 640)
        p.line(230, 620, 210, 640)
    p.drawString(260, 625, 'KEYBOARD:')
    p.rect(340, 620, 20, 20)
    if(machine.request.need_keyboard):
        p.line(340, 620, 360, 640)
        p.line(360, 620, 340, 640)
    p.drawString(400, 625, 'ETHERNET:')
    p.rect(480, 620, 20, 20)
    if(machine.request.need_ethernet):
        p.line(480, 620, 500, 640)
        p.line(500, 620, 480, 640)
    p.drawString(30, 600, 'REQUEST:')
    p.line(120, 598, 600, 598)
    p.drawString(130, 600, str(machine.request))
    p.drawString(30, 575, 'SUPPLIED:')
    p.drawString(80, 550, 'CPU:')
    p.line(120, 547, 320, 547)
    p.drawString(130, 550, str(machine.cpu))
    p.drawString(80, 525, 'RAM:')
    p.line(120, 523, 320, 523)
    p.drawString(130, 525, str(machine.ram_human()))
    p.drawString(330, 525, 'HHD:')
    p.line(370, 523, 570, 523)
    p.drawString(380, 525, str(machine.hdd_human()))
    p.drawString(80, 500, 'OS:')
    p.line(120, 498, 260, 498)
    p.drawString(130, 500, str(machine.request.os))
    p.drawString(30, 475, 'NOTES:')
    notes = p.beginText(30, 450)
    for line in str(machine.notes).splitlines():
        notes.textLine(line)
    p.drawText(notes)
    p.showPage()
    p.save()
    pdf = response_buffer.getvalue()
    response_buffer.close()
    response.write(pdf)
    return response