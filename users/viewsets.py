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
from users.serializer import  BlockdateSerializer, BlockedDateSerializer, PilgrimSerializer, PilgrimstatsSerializer, UserPilgrimStatsSerializer, UsersSerializer
from rest_framework.pagination import PageNumberPagination


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
        data = request.data
        response_data = []

        try:
            with transaction.atomic():
                for item in data:
                    instance = self.get_object_from_data(item)  # Get the instance to be updated
                    serializer = self.get_serializer(instance, data=item, partial=True)
                    serializer.is_valid(raise_exception=True)
                    self.perform_update(serializer)  # Perform the update
                    response_data.append(serializer.data)  # Collect the updated data   

                    # Update related PilgrimStats if 'pilgrim_count' is present
                    if 'pilgrim_count' in item:
                        pilgrimstats = PilgrimStats.objects.filter(
                            user=request.user, 
                            booked_datetime=instance.booked_datetime.date()
                        ).first()
                        
                        if pilgrimstats:
                            pilgrimstats.pilgrim_count = item.get('pilgrim_count')
                            pilgrimstats.save()

            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
        instance = self.get_object()  # Retrieve the object to be deleted
        booked_date = instance.booked_datetime

        # Perform the deletion of the instance
        self.perform_destroy(instance)

        # Check if there is a PilgrimStats entry for the user on the booked date
        pilgrim_stats = PilgrimStats.objects.filter(user=instance.user, booked_datetime=booked_date.date()).first()

        # Get other pilgrims booked at the same time and ordered by datetime
        other_pilgrims = Pilgrim.objects.filter(user=request.user, booked_datetime=booked_date).order_by("booked_datetime")

        if other_pilgrims.exists():  # Check if there are other pilgrims for this user
            next_master_pilgrim = other_pilgrims.first()  # Get the first pilgrim to become the new master
            next_master_pilgrim.is_master = True  # Set as the new master
            next_master_pilgrim.save()

            if pilgrim_stats:
                pilgrim_stats.pilgrim_count = other_pilgrims.count()  # Update the pilgrim count
                pilgrim_stats.save()
        else:
            if pilgrim_stats:
                pilgrim_stats.delete()  # Delete the stats if no other pilgrims exist

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
    serializer_class = BlockdateSerializer
    # filter_backends = [DjangoFilterBackend]
    # filterset_class = PilgrimStatsFilter
    
    
    def get_queryset(self):
        queryset = Blockdate.objects.filter(
            user=self.request.user
        )
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        booked=PilgrimStats.objects.filter(user=request.user).values_list("booked_datetime",flat=True)
        
        return Response({"Blocked":serializer.data,"Booked": booked if booked else []})
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = BlockdateSerializer(data=request.data,context={'request':request})
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)    
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
    
class UserPilgrimStatsPagination(PageNumberPagination):
    page_size = 10  # Default page size
    page_size_query_param = 'page_size'  # Allow clients to set the page size
    max_page_size = 100  # Maximum page size

class UserPilgrimStatsViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    pagination_class = UserPilgrimStatsPagination
    serializer_class = UserPilgrimStatsSerializer

    # Define a default queryset
    queryset = UserProfile.objects.all()  # Default queryset for the viewset

    def get_queryset(self):
        # Check if the user is an admin
        is_admin = self.request.user.is_superuser

        if is_admin:
            return UserProfile.objects.all()
        else:
            return UserProfile.objects.filter(id=self.request.user.user_id)

    @action(detail=False, methods=['get'], url_path='users')
    def list_users(self, request, *args, **kwargs):
        user_data = UserPilgrimStatsSerializer(request.user).data
        return Response(user_data)
        # If the user is an admin, return the list of users
        if request.user.is_superuser:
            queryset = self.get_queryset()
            response_data = UserPilgrimStatsSerializer(queryset, many=True).data
            return Response(response_data)
        else:
            # If the user is not an admin, return their own details
            user_data = UserPilgrimStatsSerializer(request.user).data
            return Response(user_data)

    @action(detail=False, methods=['get'], url_path='pilgrims')
    def list_pilgrims(self, request, *args, **kwargs):
        # Get current year and month
        current_year = datetime.now().year
        current_month = datetime.now().month

        # Get year and month from query params or use current values
        year = request.query_params.get('year', current_year)
        month = request.query_params.get('month', current_month)

        if request.user.is_superuser:
            # If the user is a superuser, get the user ID from the query parameters
            user_id = request.query_params.get('user_id')
            if user_id is None:
                return Response({"detail": "User ID is required for superuser to view pilgrim details."}, status=status.HTTP_400_BAD_REQUEST)

            # Get the pilgrims for the specified user
            pilgrims = Pilgrim.objects.filter(user_id=user_id, booked_datetime__year=int(year), booked_datetime__month=int(month))
        else:
            # If the user is not an admin, return their pilgrims
            pilgrims = Pilgrim.objects.filter(user=request.user, booked_datetime__year=int(year), booked_datetime__month=int(month))

        # Apply pagination
        page = self.paginate_queryset(pilgrims)
        if page is not None:
            serializer = PilgrimSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # If no pagination is applied, return all data
        serializer = PilgrimSerializer(pilgrims, many=True)
        return Response(serializer.data)