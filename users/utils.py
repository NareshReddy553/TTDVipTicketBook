import hashlib, base64
from io import BytesIO
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import os

def get_hashed_password(password):
    m = hashlib.sha256()
    m.update(settings.PASSWORD_SALT)
    m.update(password.encode('utf-8'))
    hash = m.digest()
    pwdHash = base64.b64encode(hash).decode('utf-8')
    return pwdHash

import calendar
from datetime import date

def get_weekend_dates_for_year(year):
    weekends = []
    for month in range(1, 13):
        cal = calendar.monthcalendar(year, month)
        for week in cal:
            if week[calendar.SATURDAY] != 0:
                weekends.append(date(year, month, week[calendar.SATURDAY]))
            if week[calendar.SUNDAY] != 0:
                weekends.append(date(year, month, week[calendar.SUNDAY]))
    return weekends

def get_weekend_dates_for_month(year, month):
    weekends = []
    cal = calendar.monthcalendar(year, month)
    for week in cal:
        if week[calendar.SATURDAY] != 0:
            weekends.append(date(year, month, week[calendar.SATURDAY]))
        if week[calendar.SUNDAY] != 0:
            weekends.append(date(year, month, week[calendar.SUNDAY]))
    return weekends




def render_to_pdf(template_src, context_dict={}):
    html = render_to_string(template_src, context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


import os
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib.staticfiles import finders
from django.utils._os import safe_join
from django.core.exceptions import SuspiciousFileOperation


def link_callback(uri, rel):
        """
        Convert HTML URIs to absolute system paths so xhtml2pdf can access those
        resources
        """
    
        if uri.startswith(settings.STATIC_URL):
            path = uri.replace(settings.STATIC_URL, "")
            safe_path = safe_join(settings.STATIC_ROOT, path)
        elif uri.startswith(settings.MEDIA_URL):
            path = uri.replace(settings.MEDIA_URL, "")
            safe_path = safe_join(settings.MEDIA_ROOT, path)
        else:
            return uri

        # Make sure the resulting path is within the base directory
        try:
            if not os.path.isfile(safe_path):
                raise SuspiciousFileOperation(f"The file {safe_path} does not exist")
        except SuspiciousFileOperation:
            return uri

        return safe_path
    
    
from datetime import datetime

def get_date_from_string(date_string, date_format="%Y-%m-%d %H:%M:%S"):
    parsed_datetime = datetime.strptime(date_string, date_format)
    return parsed_datetime.date()


import qrcode
import base64
from io import BytesIO
from django.shortcuts import render

def generate_qr_code(request, hash_key):
    # The URL or data you want to encode in the QR code
    data = f"{request.build_absolute_uri('/')}api/users/qr-verify/{hash_key}/"

    # Generate the QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Create an image from the QR code instance
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert the image to a BytesIO object
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return img_str