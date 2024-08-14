from datetime import datetime,date
from rest_framework import serializers
import uuid

from config.settings import MLA_QUOTA_BOOK_FOR_DAY,MP_QUOTA_BOOK_FOR_DAY
from users.models import Blockdate, Pilgrim, UserProfile,PilgrimStats
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from users.utils import get_date_from_string



class UsersProfileSerializer(serializers.ModelSerializer):    
    
    class Meta:
        model = UserProfile
        fields = ['user_id','is_superuser','is_mla','email','constituency','email','first_name','last_name','username']

class UsersSerializer(serializers.ModelSerializer):
    username=serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True, max_length=100)
    last_name = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=100)
    phone_number = serializers.CharField(required=False, allow_null=True)
    created_datetime = serializers.DateTimeField(required=False, allow_null=True)
    modified_datetime = serializers.DateTimeField(required=False, allow_null=True)
    
    
    class Meta:
        model = UserProfile
        exclude=['groups','user_permissions','is_staff',]
    
    @transaction.atomic
    def create(self, validated_data,*args, **kwargs):
        password = validated_data.pop('password', None)
        instance =get_user_model()(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance
    
        
class PilgrimstatsSerializer(serializers.ModelSerializer):
    is_blocked=serializers.SerializerMethodField()
            
    class Meta:
        model = PilgrimStats
        fields=["pilgrimstat_id","booked_datetime","pilgrim_count","is_blocked"]
        
    def get_is_blocked(self, obj):

        # Filter the blocked dates
        blocked_qs = Blockdate.objects.filter(user=obj.user,blockdate=obj.booked_datetime)
        
        # Serialize if there are results
        if blocked_qs.exists():
           return True
        return False
        
class BulkPilgrimsSerializer(serializers.ListSerializer):

    def create(self, validated_data):
        user = self.context['request'].user
        hash_key = uuid.uuid4().hex
        pilgrims = [Pilgrim(**item, user=user,hash_key=hash_key) for item in validated_data]
        created_pilgrims = Pilgrim.objects.bulk_create(pilgrims)

        total_pilgrim_count=int(self.context['request'].data.get('pilgrim_count'))
        booked_datetime=self.context['request'].data.get('booked_datetime')
        if booked_datetime:
            booked_date=get_date_from_string(booked_datetime,"%Y-%m-%d")
        
        if total_pilgrim_count:
            PilgrimStats.objects.create(booked_datetime=booked_date,
                user=user,pilgrim_count=total_pilgrim_count)
            
        # stats_dict = {}
        # for pilgrim in created_pilgrims:
        #     key = (pilgrim.booked_datetime.date(), user.pk)
        #     pilgrimstats_qs=PilgrimStats.objects.filter(booked_datetime=pilgrim.booked_datetime.date(),user=user).first()
        #     if pilgrimstats_qs is not None:
        #         if key not in stats_dict:
        #             stats_dict[key] = {
        #                 'booked_count': pilgrimstats_qs.booked_count,
        #                 'vacant_count': pilgrimstats_qs.vacant_count
        #             }
        #     else:
        #         if key not in stats_dict:
        #             stats_dict[key] = {
        #             'booked_count': 0,
        #             'vacant_count': MLA_QUOTA_BOOK_FOR_DAY if user.is_mla else MP_QUOTA_BOOK_FOR_DAY
        #         }
                
            
            

        #     stats_dict[key]['booked_count'] += 1
        #     stats_dict[key]['vacant_count'] -= 1

        # for key, value in stats_dict.items():
        #     booked_date, user_id = key
        #     stats, created = PilgrimStats.objects.update_or_create(
        #         booked_datetime=booked_date,
        #         user=user,
        #         defaults={'booked_count': value['booked_count'], 'vacant_count': value['vacant_count']},
        #         )
                

        return created_pilgrims
    

class PilgrimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pilgrim
        fields = "__all__"
        list_serializer_class = BulkPilgrimsSerializer
        
\

class BlockdateSerializer(serializers.Serializer):
    dates = serializers.ListField(child=serializers.DateField())

    def create(self, validated_data):
        dates = validated_data.pop('dates', [])
        user = self.context['request'].user  # Assuming user is authenticated
        
        # Create Blockdate instances for each date in dates list
        blockdate_objs = [
            Blockdate(blockdate=date, user=user)
            for date in dates
        ]
        
        # Bulk create Blockdate instances
        blockdates = Blockdate.objects.bulk_create(blockdate_objs)

        return blockdates
    
class BlockedDateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Blockdate
        fields = ['user', 'blockdate']
        read_only_fields = ['user']
    
    


class PasswordResetSerializer(serializers.Serializer):
    username=serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True, min_length=8)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def save(self, user):
        if 'username' in self.validated_data:
            user.username = self.validated_data['username']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user