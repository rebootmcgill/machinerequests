import os
from datetime import date
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.views.generic import ListView, DetailView, CreateView
from machinerequests.models import Request, Machine
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.contrib.staticfiles import finders
from django.shortcuts import get_object_or_404
from django.conf import settings


from io import BytesIO


# Create your views here.


class UnfilledRequestsList(ListView):
    context_object_name = 'request_list'
    queryset = Request.objects.filter(filled=False)
    template_name = 'machine_requests/requests.html'

    def get_context_data(self, **kwargs):
        context = super(UnfilledRequestsList, self).get_context_data(**kwargs)
        context['page_title'] = "Unfulfilled Requests"
        return context


class ArchivedRequestsList(ListView):
    context_object_name = 'request_list'
    queryset = Request.objects.filter(filled=True)
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
    response['Content-Disposition'] = 'filename="request-' + str(machine.id) + '.pdf"'
    response_buffer = BytesIO()
    p = canvas.Canvas(response_buffer, pagesize=letter)
    #p.drawImage(finders.find("img/logo.png"), 50, 50)
    p.setLineWidth(.3)
    p.setFont('Helvetica', 12)
    p.drawString(30, 750, 'OFFICIAL COMMUNIQUE')
    p.drawString(30, 735, 'OF REBOOT')
    p.drawString(500, 750, str(date.today()))
    p.line(480, 747, 580, 747)
    p.drawString(480, 725, 'ORDER #' + str(machine.id))
    p.line(450, 723, 550, 723)
    p.drawString(30, 703, 'ORDERED BY:')
    p.line(120, 700, 220, 700)
    p.drawString(130, 703, str(machine.request.full_name()))
    p.drawString(250, 703, 'FACULTY:')
    p.line(300, 700, 600, 700)
    p.drawString(310, 703, str(machine.request.faculty_and_dept))
    p.drawString(30, 675, 'FULFILLED BY:')
    p.line(120, 672, 320, 672)
    p.drawString(120, 703, str(machine.fulfiller.get_full_name()))
    p.drawString(30, 650, 'PERIPHERALS:')
    p.rect(50, 625, 550, 25)
    p.drawString(100, 630, 'DISPLAY:')
    p.rect(120, 620, 20, 20)
    if(machine.request.need_display):
        p.line(120, 620, 140, 640)
        p.line(140, 620, 120, 640)
    p.drawString(200, 630, 'MOUSE:')
    p.rect(220, 620, 20, 20)
    if(machine.request.need_mouse):
        p.line(220, 620, 240, 640)
        p.line(240, 620, 220, 640)
    p.drawString(300, 630, 'KEYBOARD:')
    p.rect(320, 620, 20, 20)
    if(machine.request.need_keyboard):
        p.line(320, 620, 340, 640)
        p.line(340, 620, 320, 640)
    p.drawString(400, 630, 'ETHERNET:')
    p.rect(420, 620, 20, 20)
    if(machine.request.need_ethernet):
        p.line(420, 620, 440, 640)
        p.line(440, 620, 420, 640)
    p.drawString(30, 600, 'REQUEST:')
    p.line(120, 598, 620, 598)
    p.drawString(130, 600, str(machine.request))
    p.drawString(30, 575, 'SUPPLIED:')
    p.drawString(80, 550, 'CPU:')
    p.line(120, 547, 230, 547)
    p.drawString(130, 550, str(machine.cpu))
    p.drawString(230, 550, 'RAM:')
    p.line(320, 547, 430, 547)
    p.drawString(330, 550, str(machine.ram_human()))
    p.drawString(430, 550, 'HHD:')
    p.line(520, 547, 630, 547)
    p.drawString(530, 550, str(machine.hdd_human()))
    p.drawString(30, 525, 'NOTES:')
    p.drawString(30, 500, str(machine.notes))
    p.showPage()
    p.save()
    pdf = response_buffer.getvalue()
    response_buffer.close()
    response.write(pdf)
    return response