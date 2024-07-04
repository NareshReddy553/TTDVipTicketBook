from django.urls import include, path
from rest_framework import routers

from users.views import PasswordResetView, UserProfileView
from users.viewsets import BlockDateViewSet, PilgrimStatsViewSet, PilgrimsViewSet, UserProfileViewSet

router = routers.SimpleRouter()
router.register(r'usersProfile', UserProfileViewSet)
router.register(r'pilgrims', PilgrimsViewSet)
router.register(r'pilgrimstats', PilgrimStatsViewSet)
router.register(r'blockdates',BlockDateViewSet)


urlpatterns = [
        path('profile/', UserProfileView.as_view(), name='user-details'),
        path('usersProfile/<int:pk>/reset_password/', PasswordResetView.as_view(), name='reset_password'),
    ]
urlpatterns += router.urls