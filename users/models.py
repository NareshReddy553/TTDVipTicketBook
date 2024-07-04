from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager

class UserProfile(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(_("email address"), unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_mla = models.BooleanField(default=True)
    created_datetime = models.DateTimeField(blank=True, null=True)
    modified_datetime = models.DateTimeField(blank=True, null=True)
    password = models.CharField(_("password"), max_length=128)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=10,blank=True, null=True)
    constituency = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()
    
    def __str__(self):
        return self.email
    class Meta:
        managed = False
        db_table = 'userprofile'
        

class Pilgrim(models.Model):
    pilgrim_id = models.AutoField(primary_key=True)
    pilgrim_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=10, blank=True, null=True)
    aadhaar_number = models.CharField(max_length=12,unique=True)
    age = models.IntegerField(blank=True, null=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='pilgrims')
    booked_datetime = models.DateTimeField()
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)
    gender = models.CharField(max_length=1, blank=True, null=True)
    seva = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed=False
        db_table = 'pilgrims'

class PilgrimStats(models.Model):
    pilgrimstat_id = models.AutoField(primary_key=True)
    booked_datetime = models.DateField()
    booked_count = models.IntegerField(default=0)
    vacant_count = models.IntegerField(default=0)
    pilgrim = models.ForeignKey(Pilgrim, on_delete=models.DO_NOTHING, related_name='stats')
    user = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING, related_name='pilgrimstats')
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        managed=False
        db_table = 'pilgrimstats'
        
        
class Blockdate(models.Model):
    bookdate_id = models.AutoField(primary_key=True)
    blockdate = models.DateField()
    user = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING, related_name='blockdate')
    created_datetime = models.DateTimeField(blank=True, null=True)
    modified_datetime = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'BlockDate'
        unique_together = ('user', 'blockdate')