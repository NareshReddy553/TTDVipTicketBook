
from rest_framework import serializers

from config.settings import MLA_QUOTA_BOOK_FOR_DAY,MP_QUOTA_BOOK_FOR_DAY
from users.models import Pilgrim, UserProfile,PilgrimStats
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from users.utils import get_hashed_password


class UsersProfileSerializer(serializers.ModelSerializer):    
    
    class Meta:
        model = UserProfile
        fields = ['user_id','is_superuser','is_mla','email']

class UsersSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True, max_length=100)
    last_name = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=100)
    phone_number = serializers.IntegerField(required=False, allow_null=True)
    created_datetime = serializers.DateTimeField(required=False, allow_null=True)
    modified_datetime = serializers.DateTimeField(required=False, allow_null=True)
    
    
    class Meta:
        model = UserProfile
        fields = "__all__"
    
    @transaction.atomic
    def create(self, validated_data,*args, **kwargs):
        password = validated_data.pop('password', None)
        instance =get_user_model()(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance
    
    @transaction.atomic
    def update(self, instance, validated_data,*args, **kwargs):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance
    


        
        
class PilgrimstatsSerializer(serializers.ModelSerializer):
    
    
    
    class Meta:
        model = PilgrimStats
        exclude = ['user']
        
        
class BulkPilgrimsSerializer(serializers.ListSerializer):

    def create(self, validated_data):
        user = self.context['request'].user
        pilgrims = [Pilgrim(**item, user=user) for item in validated_data]
        created_pilgrims = Pilgrim.objects.bulk_create(pilgrims)

        stats_dict = {}
        for pilgrim in created_pilgrims:
            key = (pilgrim.booked_datetime.date(), user.pk)
            if key not in stats_dict:
                stats_dict[key] = {
                    'booked_count': 0,
                    'vacant_count': MLA_QUOTA_BOOK_FOR_DAY if user.is_mla else MP_QUOTA_BOOK_FOR_DAY
                }

            stats_dict[key]['booked_count'] += 1
            stats_dict[key]['vacant_count'] -= 1

        for key, value in stats_dict.items():
            booked_date, user_id = key

            # Update or create Pilgrimstats
            stats, created = PilgrimStats.objects.get_or_create(
                booked_datetime=booked_date,
                user=user,
                defaults={'booked_count': value['booked_count'], 'vacant_count': MLA_QUOTA_BOOK_FOR_DAY if user.is_mla else MP_QUOTA_BOOK_FOR_DAY - value['booked_count']}
            )
            if not created:
                stats.booked_count += value['booked_count']
                stats.vacant_count -= value['booked_count']
                if stats.vacant_count < 0:
                    raise ValueError("Vacant count cannot be negative.")
                stats.save()

        return created_pilgrims
    

class PilgrimSerializer(serializers.ModelSerializer):
    user=UsersSerializer(read_only=True)
    class Meta:
        model = Pilgrim
        fields = '__all__'
        list_serializer_class = BulkPilgrimsSerializer