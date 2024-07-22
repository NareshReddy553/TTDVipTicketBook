from io import BytesIO
from datetime import datetime
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes
from config import settings

from users.models import Pilgrim, UserProfile
from users.serializer import  PasswordResetSerializer, UsersProfileSerializer
from users.utils import get_weekend_dates_for_month, get_weekend_dates_for_year, link_callback, render_to_pdf
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import os
from django.template.loader import get_template



class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UsersProfileSerializer(user)
        return Response(serializer.data)
    
    
class PasswordResetView(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user_id = kwargs.get('pk')
        user = UserProfile.objects.get(pk=user_id)

        # Only allow the user themselves or superuser to reset the password
        if request.user != user and not request.user.is_superuser:
            return Response({"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)

        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET'])
def Blockdates_on_month_or_year(request):
    year = request.query_params.get('year')
    month = request.query_params.get('month')
    
    if not year:
        return Response({"error": "Year is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        year = int(year)
    except ValueError:
        return Response({"error": "Invalid year format"}, status=status.HTTP_400_BAD_REQUEST)

    if month:
        try:
            month = int(month)
            weekends = get_weekend_dates_for_month(year, month)
        except ValueError:
            return Response({"error": "Invalid month format"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        weekends = get_weekend_dates_for_year(year)

    weekends = [date.isoformat() for date in weekends]  # Convert to string format
    
    return Response({"weekend_dates": weekends}, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_vip_darshan_letter(request):
    data=request.data
    pilgrims_qs=Pilgrim.objects.filter(user=request.user,pilgrim_id__in=data.get('pilgrim_id'))
    if pilgrims_qs:
        accommodation_date = datetime.strptime(data.get('accommodation_date'), "%Y-%m-%d").date() if data.get('accommodation_date') else None
        darshan_date = datetime.strptime(data.get('darshan_date'), "%Y-%m-%d").date() if data.get('darshan_date') else None
    
        context = {
            'date': datetime.now().strftime("%d.%m.%Y"),
            'pilgrims': pilgrims_qs,
            'accommodation_date':accommodation_date,
            'darshan_date':darshan_date,
            'email': data.get('email'),
            'contact': data.get('contact')
        }
   
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="vip_darshan_letter.pdf"'
    # find the template and render it.
    template = get_template('vip_darshan_letter.html')
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response,link_callback=link_callback)
    # if error then show some funny view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response