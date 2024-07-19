from django.urls import include, path
from rest_framework import routers

from users.views import PasswordResetView, UserProfileView, generate_vip_darshan_letter
from users.viewsets import BlockDateViewSet, PilgrimStatsViewSet, PilgrimsViewSet, UserProfileViewSet

router = routers.SimpleRouter()
router.register(r'usersProfile', UserProfileViewSet)
router.register(r'pilgrims', PilgrimsViewSet)
router.register(r'pilgrimstats', PilgrimStatsViewSet)
router.register(r'blockdates',BlockDateViewSet)


urlpatterns = [
        path('profile/', UserProfileView.as_view(), name='user-details'),
        path('usersProfile/<int:pk>/reset_password/', PasswordResetView.as_view(), name='reset_password'),
        path('vip-darshan-letter/', generate_vip_darshan_letter, name='vip_darshan_letter'),
    ]
urlpatterns += router.urls