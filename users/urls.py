from django.urls import include, path
from rest_framework import routers

from users.views import UserProfileView
from users.viewsets import BlockDateViewSet, PilgrimStatsViewSet, PilgrimsViewSet, UserProfileViewSet

router = routers.SimpleRouter()
router.register(r'usersProfile', UserProfileViewSet)
router.register(r'upilgrims', PilgrimsViewSet)
router.register(r'pilgrimstats', PilgrimStatsViewSet)
router.register(r'blockdates',BlockDateViewSet)


urlpatterns = [
        path('profile/', UserProfileView.as_view(), name='user-details'),
    ]
urlpatterns += router.urls