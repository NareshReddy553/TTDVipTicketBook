import django_filters
from users.models import PilgrimStats

class PilgrimStatsFilter(django_filters.FilterSet):
    booked_datetime = django_filters.DateFilter(field_name='booked_datetime')

    class Meta:
        model = PilgrimStats
        fields = ['booked_datetime']