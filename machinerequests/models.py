from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.core.mail import EmailMessage
from machinerequests.functions import generate_reciept_pdf
from django.template.loader import render_to_string
from django.db.models.signals import post_save
from django.dispatch import receiver
from publicreboot.models import OfficeHours
# Create your models here.


class CPU(models.Model):
    name = models.CharField(max_length=64)
    cores = models.PositiveSmallIntegerField()
    x64 = models.BooleanField(default=True)
    clock = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return self.name + ' - ' + str(self.clock) + 'GHz'


class OperatingSystem(models.Model):
    name = models.CharField(max_length=64)
    version = models.CharField(max_length=32)
    experimental = models.BooleanField(default=False)

    def __str__(self):
        exp = ''
        if self.experimental:
            exp = '[Experimental]'
        return exp + str(self.name) + ' - ' + str(self.version)


class Preset(models.Model):
    cpu = models.ForeignKey(CPU)
    ram = models.PositiveIntegerField()
    hdd = models.PositiveIntegerField()

    def ram_human(self):
        if(self.ram >= 1024):
            return str(self.ram / 1024.0) + 'GB'
        else:
            return str(self.ram) + 'MB'

    def hdd_human(self):
        if(self.hdd >= 1024):
            return str(self.hdd / 1024.0) + 'TB'
        else:
            return str(self.hdd) + 'GB'

    def __str__(self):
        return str(self.cpu) + ' - RAM: ' + self.ram_human() + ' - HDD: ' + self.hdd_human()


class Request(models.Model):
    GRADUATE = 'G'
    UNDERGRAD = 'U'
    FACULTY_MEMBER = 'F'
    NON_FACULTY_STAFF = 'S'
    OTHER = 'O'
    REQUESTER_TYPE_CHOICES = (
        (GRADUATE, 'Graduate Student'),
        (UNDERGRAD, 'Undergrad Student'),
        (FACULTY_MEMBER, 'Faculty Member'),
        (NON_FACULTY_STAFF, 'Non-Faculty Staff Member'),
        (OTHER, 'Other'),
    )
    family_name = models.CharField(max_length=32)
    given_name = models.CharField(max_length=32)
    email = models.EmailField(max_length=254)
    requester_type = models.CharField(max_length=1, choices=REQUESTER_TYPE_CHOICES)
    faculty_and_dept = models.CharField(max_length=256)
    organization = models.CharField(max_length=32, blank=True)
    preset = models.ForeignKey(Preset)
    os = models.ForeignKey(OperatingSystem, blank=True, null=True, default=2)
    machine_use = models.TextField()
    need_display = models.BooleanField(default=False)
    need_mouse = models.BooleanField(default=False)
    need_keyboard = models.BooleanField(default=False)
    need_ethernet = models.BooleanField(default=False)
    extra_information = models.TextField(blank=True)
    amount = models.PositiveIntegerField(default=1)
    filled = models.BooleanField(default=False)
    filled_at = models.DateTimeField(null=True)
    requested_at = models.DateTimeField(auto_now_add=True)

    def fulfill(self):
        self.filled = True
        self.filled_at = timezone.now()
        self.save()
        for machine in self.machine_set.all():
            machine.notify()

    def full_name(self):
        return str(self.given_name) + ' ' + str(self.family_name)

    def get_machines(self):
        return self.machine_set.all()

    def get_fulfill_url(self):
        return self.get_absolute_url() + 'fulfill/'

    def get_fulfill_mark_url(self):
        return self.get_absolute_url() + 'mark/'

    def picked_up(self):
        for machine in self.machine_set.all():
            if not machine.picked_up:
                return False
        return True

    def __str__(self):
        return str(self.preset) + ' for ' + str(self.given_name) + ' ' + str(self.family_name)

    def get_absolute_url(self):
        return reverse('Request-Details', args=[str(self.id)])

    def acknowedge(self):
        body = render_to_string('machine_requests/ack.mail', {'request': self,
            'office_hours': OfficeHours.objects.all()})
        email = EmailMessage("Your Request has been recieved", body, 'reboot@mcgilleus.ca', [self.email],
            ['reboot@mcgilleus.ca'], headers={'Reply-To': 'reboot@mcgilleus.ca'})
        email.send()


@receiver(post_save, sender=Request)
def creation_acknowedge_hook(sender, **kwargs):
    if kwargs["created"]:
        kwargs["instance"].acknowedge()


class Machine(models.Model):
    request = models.ForeignKey(Request)
    fulfiller = models.ForeignKey(User)
    cpu = models.ForeignKey(CPU)
    ram = models.PositiveIntegerField()
    hdd = models.PositiveIntegerField()
    pickedup_at = models.DateTimeField(null=True)

    def pickup(self):
        self.picked_up = True
        self.pickedup_at = timezone.now()
        self.save()

    def ram_human(self):
        if(self.ram >= 1024):
            return str(self.ram / 1024.0) + 'GB'
        else:
            return str(self.ram) + 'MB'

    def hdd_human(self):
        if(self.hdd >= 1024):
            return str(self.hdd / 1024.0) + 'TB'
        else:
            return str(self.hdd) + 'GB'

    notes = models.TextField(blank=True)
    picked_up = models.BooleanField(default=False)

    def __str__(self):
        return str(self.request) + ' Forfilled by ' + str(self.fulfiller)

    def get_absolute_url(self):
        return reverse('Machine-Details', args=[str(self.id)])

    def get_pickup_url(self):
        return self.get_absolute_url() + 'pickup/'

    def get_pdf_url(self):
        return self.get_absolute_url() + 'pdf/'

    def notify(self):
        body = render_to_string('machine_requests/email.mail', {'machine': self})
        reciept = generate_reciept_pdf(self)
        email = EmailMessage("Your Machine is Ready", body, 'reboot@mcgilleus.ca', [self.request.email],
            ['reboot@mcgilleus.ca'], headers={'Reply-To': 'reboot@mcgilleus.ca'})
        email.attach('Machine-reciept.pdf', reciept)
        email.send()