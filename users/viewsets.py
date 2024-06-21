import logging
import os
from datetime import date, datetime
from math import trunc
from django.db import transaction

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, APIException
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Case, Count, Q, Value, When
from django.db.models.expressions import F, OuterRef, Subquery
from django.db.models.functions import Concat
from django.db.transaction import atomic
from django.http.response import JsonResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import IntegerField
from rest_framework import permissions
from django_filters.rest_framework import DjangoFilterBackend
from users.filters import PilgrimStatsFilter
from users.models import Pilgrim, PilgrimStats, UserProfile
from users.serializer import PilgrimSerializer, PilgrimstatsSerializer, UsersSerializer


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
        
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({"message": "User updated successfully"}, status=status.HTTP_200_OK)
        except APIException as e:
            return Response({"message": "Failed to update user", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        
    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    

class PilgrimsViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Pilgrim.objects.all()
    serializer_class = PilgrimSerializer
    
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response( status=status.HTTP_201_CREATED, headers=headers)
        except APIException as e:
            return Response({"message": "Failed to Book", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        
        


class PilgrimStatsViewSet(viewsets.ModelViewSet):
    queryset = PilgrimStats.objects.all()
    serializer_class = PilgrimstatsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PilgrimStatsFilter
    
    