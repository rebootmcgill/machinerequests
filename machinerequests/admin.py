from django.contrib import admin
from machinerequests.models import CPU, OperatingSystem, Preset, Request, Machine
# Register your models here.


class CPUAdmin(admin.ModelAdmin):
    fields = ('name', 'clock', 'cores', 'x64')
    list_display = ('__str__', 'cores', 'x64')
    experimental = ('x64', 'cores')

admin.site.register(CPU, CPUAdmin)


class OSAdmin(admin.ModelAdmin):
    fields = ('name', 'version', 'experimental')
    list_display = ('name', 'version')
    list_filter = ('experimental',)
    search_fields = ('name',)

admin.site.register(OperatingSystem, OSAdmin)


class PresetAdmin(admin.ModelAdmin):
    fields = ('cpu', 'ram', 'hdd')
    list_display = ('cpu', 'ram_human', 'hdd_human')
    list_filter = ('cpu__x64', 'cpu__cores')

admin.site.register(Preset, PresetAdmin)


class RequestAdmin(admin.ModelAdmin):
    readonly_fields = ('family_name', 'given_name', 'organization', 'preset', 'machine_use', 'extra_information',
        'requested_at', 'filled_at')
    fields = ('email', 'requester_type', 'faculty_and_dept', 'amount', 'filled', 'family_name', 'given_name',
        'organization', 'preset', 'os', 'machine_use', 'need_display', 'need_mouse', 'need_keyboard', 'need_ethernet',
        'extra_information', 'requested_at', 'filled_at')
    list_display = ('family_name', 'given_name', 'preset', 'os', 'need_display', 'need_mouse', 'need_keyboard',
        'need_ethernet', 'amount', 'filled', 'requested_at')
    list_filter = ('preset', 'os', 'need_display', 'need_mouse', 'need_keyboard', 'need_ethernet', 'filled')
    search_fields = ('family_name', 'given_name', 'email', 'organization')

admin.site.register(Request, RequestAdmin)


class MachineAdmin(admin.ModelAdmin):
    fields = ('request', 'fulfiller', 'cpu', 'ram', 'hdd', 'notes', 'picked_up')
    list_display = ('request', 'fulfiller', 'picked_up')
    list_filter = ('picked_up',)
    search_fields = ('request__family_name', 'request__given_name', 'forfiller')

admin.site.register(Machine, MachineAdmin)
