import hashlib, base64
from django.conf import settings

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
