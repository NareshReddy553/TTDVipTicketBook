import logging
from datetime import datetime
from django.contrib.auth.backends import BaseBackend
from config import settings
from django.contrib.auth import get_user_model

from users.models import UserProfile
from users.utils import get_hashed_password
from rest_framework_simplejwt.authentication import (
    AuthenticationFailed,
    InvalidToken,
    JWTAuthentication,
    api_settings,
)
from django.core.cache import cache

logger = logging.getLogger("account.backends")
user_cache_prefix = "USER_CACHE_"
role_cache = "ROLE_CACHE"

# def prep_user(self, user):
#         user.is_authenticated = True

#         user_cache_name = user_cache_prefix + str(user.user_id)
#         cache.set(user_cache_name, user, settings.USER_CACHE_TTL)

#         return user

# class AccountBackend(BaseBackend):
    # def authenticate(self, request, username, password, **kwargs):
    #     # 1. get UserProfile and UserPassword by username
    #     logger.debug("username: " + username)

    #     try:
    #         user = Users.objects.get(
    #             email__iexact=username,
    #             is_active=True,
    #         )
    #     except Users.DoesNotExist:
    #         return None

    #     if user is None:
    #         return None


    #     # 2. calculate password's hash
    #     pwdHash = get_hashed_password(password)

    #     # 3. compare UserPassword password hash and the calculated hash
    #     if pwdHash != user.password:
    #         return None

    #     if not user.is_active:
    #         raise AuthenticationFailed(_("User is inactive"), code="user_inactive")

       
    #     return self.prep_user(user)
    # def authenticate(self, request, username=None, password=None, **kwargs):
    #     User = get_user_model()
    #     try:
    #         user = User.objects.get(email=username)
    #         if user.check_password(password):
    #             return user
    #     except User.DoesNotExist:
    #         return None

    # def get_user(self, user_id):
    #     User = get_user_model()
    #     try:
    #         return User.objects.get(pk=user_id)
    #     except User.DoesNotExist:
    #         return None
    


# class AccountJWTAuthentication(JWTAuthentication):
#     def get_user(self, validated_token):
#         """
#         Attempts to find and return a user using the given validated token.
#         """
#         try:
#             user_id = validated_token[api_settings.USER_ID_CLAIM]
#         except KeyError:
#             raise InvalidToken(_("Token contained no recognizable user identification"))

#         # use memory cache for better performance
#         user_cache_name = user_cache_prefix + str(user_id)
#         user = cache.get(user_cache_name)

#         if user is None:
#             try:
#                 user = Users.objects.get(pk=user_id)
#             except Users.DoesNotExist:
#                 raise AuthenticationFailed(_("User not found"), code="user_not_found")

#             user = self.prep_user(user)
#             if not user.is_active:
#                 raise AuthenticationFailed(_("User is inactive"), code="user_inactive")

#         return user