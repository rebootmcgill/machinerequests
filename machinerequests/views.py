from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView
from machinerequests.models import Request, Machine
from django.contrib.auth.decorators import login_required

# Create your views here.

class UnfilledRequestsList(ListView):
    context_object_name = 'request_list'
    queryset = Request.objects.filter(filled=False)
    template_name = 'machine_requests/requests.html'
    def get_context_data(self, **kwargs):
        context = super(UnfilledRequestsList, self).get_context_data(**kwargs)
        context['page_title'] = "Unforfilled Requests"
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
    context_object_name = 'request'
    template_name = 'machine_requests/request_view.html'

@login_required
class MachineCreate(CreateView):
    model = Machine
    fields = ['cpu', 'ram', 'hdd', 'notes']
    template_name = 'machine_requests/machine_create.html'
    def form_valid(self, form):
        form.instance.forfiller = self.request.user
        return super(MachineCreate, self).form_valid(form)

class MachineView(DetailView):
    model = Machine
    context_object_name = 'machine'
    template_name = 'machine_requests/machine_view.html'
