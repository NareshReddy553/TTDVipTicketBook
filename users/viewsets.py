import logging
import os
from datetime import date, datetime
from math import trunc
from django.db import IntegrityError, transaction

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, APIException
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Case, Count, Q, Value, When
from django.db.models.expressions import F, OuterRef, Subquery
from django.db.models.functions import Concat
from django.db.transaction import atomic
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import IntegerField
from rest_framework import serializers
from rest_framework import permissions
from django_filters.rest_framework import DjangoFilterBackend
from users.filters import PilgrimFilter, PilgrimStatsFilter
from users.models import Blockdate, Pilgrim, PilgrimStats, UserProfile
from users.serializer import  BlockdateSerializer, BlockedDateSerializer, PilgrimSerializer, PilgrimstatsSerializer, UsersSerializer


logger = logging.getLogger("tfn.views")

class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class UserProfileViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,IsSuperUser)
    queryset = UserProfile.objects.all()
    serializer_class = UsersSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can create new users.")

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED, headers=headers)
        except APIException as e:
            return Response({"message": "Failed to create user", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
 
    
    
    

class PilgrimsViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Pilgrim.objects.all()
    serializer_class = PilgrimSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PilgrimFilter
    
    def get_queryset(self):
        queryset = Pilgrim.objects.filter(
            user=self.request.user
        )
        return queryset
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        
        serializer = self.get_serializer(data=request.data.get('pilgrims'), many=True)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response( status=status.HTTP_201_CREATED, headers=headers)
        except APIException as e:
            return Response({"message": "Failed to Book", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['put','patch'],url_path='pilgrim_update')
    def pilgrim_bulk_update(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            return self.bulk_update(request, *args, **kwargs)
        else:
            return super().update(request, *args, **kwargs)
        
        

    def bulk_update(self, request, *args, **kwargs):
        partial = request.method=='PATCH'
        data = request.data
        response_data = []
        try:
            with transaction.atomic():
                for item in data:
                    instance = self.get_object_from_data(item)
                    serializer = self.get_serializer(instance, data=item, partial=partial)
                    serializer.is_valid(raise_exception=True)
                    self.perform_update(serializer)
                    response_data.append(serializer.data)
                    if item.get('pilgrim_count'):
                        pilgrimstats=PilgrimStats.objects.filter(user=request.user,booked_datetime=instance.booked_datetime.date()).first()
                        pilgrimstats.booked_datetime=item.get('pilgrim_count')
                        pilgrimstats.save()
                
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(response_data, status=status.HTTP_200_OK)

    def get_object_from_data(self, data):
        # Assumes 'id' field is present in data to fetch the object
        obj_id = data.get('pilgrim_id')
        if not obj_id:
            raise ValueError("ID field is required for bulk update")
        try:
            return self.queryset.get(pk=obj_id)
        except Pilgrim.DoesNotExist:
            raise ValueError(f"Object with ID {obj_id} does not exist")

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        booked_date = instance.booked_datetime        
        self.perform_destroy(instance)
        pilgrimstanst=PilgrimStats.objects.filter(user=instance.user,booked_datetime=booked_date.date()).delete()
        # other_pilgrims=Pilgrim.objects.filter(user=request.user,booked_datetime=booked_date)
        # if other_pilgrims:
        #     if pilgrimstanst:
        #         pilgrimstanst.pilgrim_count =other_pilgrims.count()
                
        # else:
        #     pilgrimstanst.pilgrim_count =0
            
        # pilgrimstanst.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()
            
        
        


class PilgrimStatsViewSet(viewsets.ModelViewSet):
    queryset = PilgrimStats.objects.all()
    serializer_class = PilgrimstatsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PilgrimStatsFilter
    
    def get_queryset(self):
        queryset = PilgrimStats.objects.filter(
            user=self.request.user
        )
        return queryset
    


class BlockDateViewSet(viewsets.ModelViewSet):
    queryset = Blockdate.objects.all()
    serializer_class = BlockedDateSerializer
    # filter_backends = [DjangoFilterBackend]
    # filterset_class = PilgrimStatsFilter
    
    
    def get_queryset(self):
        queryset = Blockdate.objects.filter(
            user=self.request.user
        )
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = BlockdateSerializer(data=request.data,context={'request':request})
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        
        except Exception  as e :
                return Response({"error": e}, status=status.HTTP_400_BAD_REQUEST)    
        return Response(status=status.HTTP_201_CREATED)
    
    @transaction.atomic
    @action(detail=False, methods=['patch'], url_path='unblock')
    def unblock_dates(self, request):
        serializer = BlockdateSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            dates = serializer.validated_data['dates']
            Blockdate.objects.filter(user=request.user, blockdate__in=dates).delete()
            return Response({"status": "Dates unblocked."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)