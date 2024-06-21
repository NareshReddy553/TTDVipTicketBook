import hashlib, base64
from django.conf import settings

def get_hashed_password(password):
    m = hashlib.sha256()
    m.update(settings.PASSWORD_SALT)
    m.update(password.encode('utf-8'))
    hash = m.digest()
    pwdHash = base64.b64encode(hash).decode('utf-8')
    return pwdHash