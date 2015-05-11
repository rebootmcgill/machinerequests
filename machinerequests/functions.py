from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from machinerequests.models import Request
from django.utils import timezone
from datetime import timedelta


# -*- coding: utf-8 -*-
def generate_reciept_pdf(machine):
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
    return pdf


def get_pending_pickup_requests(filled_at=None):
    if filled_at:
        filled = Request.objects.filter(filled=True, filled_at__leq=filled_at)
    else:
        filled = Request.objects.filter(filled=True)
    pending = []
    for req in filled:
        if not req.picked_up:
            pending += [req]
    return pending


def get_old_orders(days=30):
    cutoff = timezone.now() - timedelta(days=days)
    return get_pending_pickup_requests(cutoff)


def overdue_pickup_reqs():
    return get_old_orders(60)
