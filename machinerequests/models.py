from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

# Create your models here.

class CPU(models.Model):
    name = models.CharField(max_length=64)
    cores = models.PositiveSmallIntegerField()
    x64 = models.BooleanField()
    clock = models.DecimalField(max_digits=4, decimal_places=2)
    def __str__(self):
        return self.name + ' - ' + str(self.clock) + 'GHz'

class OperatingSystem(models.Model):
    name = models.CharField(max_length=64)
    version = models.CharField(max_length=32)
    experimental = models.BooleanField(default=False)
    def __str__(self):
        return str(self.name) + ' - ' + str(self.version)

class Preset(models.Model):
    cpu = models.ForeignKey(CPU)
    ram = models.PositiveIntegerField()
    hdd = models.PositiveIntegerField()
    def ram_human(self):
        if(self.ram >= 1024):
            return str(self.ram/1024.0) + 'GB'
        else:
            return str(self.ram) + 'MB'

    def hdd_human(self):
        if(self.hdd >= 1024):
            return str(self.hdd/1024.0) + 'TB'
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
    organization = models.CharField(max_length=32)
    preset = models.ForeignKey(Preset)
    os = models.ForeignKey(OperatingSystem, blank=True, null=True)
    machine_use = models.TextField()
    need_display = models.BooleanField()
    need_mouse = models.BooleanField()
    need_keyboard = models.BooleanField()
    need_ethernet = models.BooleanField()
    extra_information = models.TextField(blank=True)
    amount = models.PositiveIntegerField()
    filled = models.BooleanField(default=False)

    def get_machines(self):
        return self.machine_set.all()

    def __str__(self):
        return self.preset + ' for ' + self.given_name + ' ' + self.family_name

    def get_absolute_url(self):
        return reverse('Request-Details', args=[str(self.id)])

class Machine(models.Model):
    request = models.ForeignKey(Request)
    forfiller = models.ForeignKey(User)
    cpu = models.ForeignKey(CPU)
    ram = models.PositiveIntegerField()
    hdd = models.PositiveIntegerField()

    def ram_human(self):
        if(self.ram >= 1024):
            return str(self.ram/1024.0) + 'GB'
        else:
            return str(self.ram) + 'MB'

    def hdd_human(self):
        if(self.hdd >= 1024):
            return str(self.hdd/1024.0).join('TB')
        else:
            return str(self.hdd).join('GB')

    notes = models.TextField(blank=True)
    picked_up = models.BooleanField(default=False)

    def __str__(self):
        return self.request + ' Forfilled by ' + self.forfiller

    def get_absolute_url(self):
        return reverse('Machine-Details', args=[str(self.id)])
