from django.forms import ModelForm
from machinerequests.models import Request, Machine

class RequestForm(ModelForm):
    class Meta:
        model = Request
        fields = ['given_name', 'family_name', 'email', 'requester_type', 'faculty_and_dept', 'organization', 'preset', 'os', 'machine_use', 'need_display', 'need_mouse', 'need_keyboard', 'need_ethernet', 'extra_information', 'amount']


class MachineForm(ModelForm):
    class Meta:
        model = Machine
        fields = ['cpu', 'ram', 'hdd', 'notes']
