from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.core.mail import EmailMessage, mail_managers
from machinerequests.functions import generate_reciept_pdf
from django.template.loader import render_to_string
from django.db.models.signals import post_save
from django.dispatch import receiver
from publicreboot.models import OfficeHours
from datetime import timedelta, datetime
from django.conf import settings
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
    os = models.ForeignKey(OperatingSystem, blank=True, null=True, default=4)
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
    failed_to_pickup = models.BooleanField(default=False)

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
        if not self.filled:
            return False
        for machine in self.machine_set.all():
            if not machine.picked_up:
                return False
        return True

    def enough(self):
        return (self.machine_set.count() == self.amount)

    enough.short_description = 'Enough Machines'
    enough.boolean = True

    def __str__(self):
        return str(self.preset) + ' for ' + str(self.given_name) + ' ' + str(self.family_name)

    def get_absolute_url(self):
        return reverse('Request-Details', args=[str(self.id)])

    def acknowedge(self):
        body = render_to_string('machine_requests/ack.mail', {'request': self,
            'office_hours': OfficeHours.objects.all()})
        email = EmailMessage("[Reboot]Your Request has been recieved", body, 'reboot@mcgilleus.ca', [self.email],
            ['reboot@mcgilleus.ca'], headers={'Reply-To': 'reboot@mcgilleus.ca'})
        email.send()

    def revoke(self):
        body = render_to_string('machine_requests/revoke.mail', {'request': self,
            'office_hours': OfficeHours.objects.all()})
        email = EmailMessage("[Reboot]Overdue pickup: machine reallocated", body, 'reboot@mcgilleus.ca', [self.email],
            ['reboot@mcgilleus.ca'], headers={'Reply-To': 'reboot@mcgilleus.ca'})
        email.send()
        self.failed_to_pickup = True
        self.save()


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

    def pending(self):
        return not (self.picked_up or self.request.failed_to_pickup)
    pending.boolean = True

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


def get_pending_pickup_requests(filled_at=None):
    if filled_at:
        filled = Request.objects.filter(filled=True, failed_to_pickup=False, filled_at__lte=filled_at,
            machine__picked_up=False).distinct().order_by('-filled_at')
    else:
        filled = Request.objects.filter(filled=True, failed_to_pickup=False,
            machine__picked_up=False).distinct().order_by('-filled_at')
    return filled


def get_old_orders(days=30):
    cutoff = timezone.now() - timedelta(days=days)
    return get_pending_pickup_requests(cutoff)


def overdue_pickup_reqs():
    return get_old_orders(60)


def audit():
    ops_phone = settings.OPS_PHONE
    now = timezone.now()
    month = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
    unfilled_count = Request.objects.filter(filled=False).count()
    pending_pickup_count = Machine.objects.filter(picked_up=False, request__failed_to_pickup=False).count()
    orders_count = Request.objects.filter(requested_at__gte=month).count()
    filled_count = Request.objects.filter(filled=True, filled_at__gte=month).count()
    pickup_count = Machine.objects.filter(picked_up=True, pickedup_at__gte=month).count()
    overdue = overdue_pickup_reqs()
    body = render_to_string('machine_requests/audit-week.mail', {'unfilled_count': unfilled_count,
            'pending_pickup_count': pending_pickup_count, 'orders_count': orders_count, 'filled_count': filled_count,
            'pickup_count': pickup_count, 'ops_phone': ops_phone, 'overdue': overdue})
    mail_managers("Weekly Audit", body)