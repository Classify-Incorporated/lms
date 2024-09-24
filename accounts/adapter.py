from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse  # Updated import
from django.contrib.auth import login
from django.shortcuts import redirect
from django.conf import settings
from .models import Profile, CustomUser
import requests
from allauth.socialaccount import app_settings
from allauth.socialaccount.providers.oauth2.views import OAuth2Adapter, OAuth2CallbackView, OAuth2LoginView
from .provider import MicrosoftProvider

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        user.email = form.cleaned_data.get('email')
        user.set_password(form.cleaned_data.get('password'))  # Ensure the password is set and hashed
        user.save()
        return user

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = sociallogin.user
        extra_data = sociallogin.account.extra_data

        user.email = extra_data.get('mail', extra_data.get('userPrincipalName', ''))
        user.first_name = extra_data.get('givenName', '')
        user.last_name = extra_data.get('surname', '')
        user.username = user.email  # Ensure username is set to the email

        return user

    def pre_social_login(self, request, sociallogin):
        email = sociallogin.account.extra_data.get('mail', sociallogin.account.extra_data.get('userPrincipalName', ''))
        try:
            user = CustomUser.objects.get(email=email)
            sociallogin.state['process'] = 'login'
            sociallogin.user = user
            user.backend = 'allauth.account.auth_backends.AuthenticationBackend'  # Specify the backend
            login(request, user)
            raise ImmediateHttpResponse(redirect('dashboard'))
        except CustomUser.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        user = sociallogin.user
        user.save()

        profile, created = Profile.objects.get_or_create(user=user)
        profile.first_name = user.first_name
        profile.last_name = user.last_name
        profile.save()

        user.backend = 'allauth.account.auth_backends.AuthenticationBackend'  # Specify the backend
        login(request, user)
        return user

class MicrosoftAuth2Adapter(OAuth2Adapter):
    provider_id = MicrosoftProvider.id

    settings = app_settings.PROVIDERS.get(provider_id, {})
    tenant = settings.get("TENANT")

    authorize_url = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize".format(tenant=tenant)
    access_token_url = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token".format(tenant=tenant)
    profile_url = "https://graph.microsoft.com/v1.0/me"

    def complete_login(self, request, app, token, **kwargs):
        headers = {'Authorization': 'Bearer {0}'.format(token.token)}
        resp = requests.get(self.profile_url, headers=headers)
        extra_data = resp.json()
        return self.get_provider().sociallogin_from_response(request, extra_data)

oauth2_login = OAuth2LoginView.adapter_view(MicrosoftAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(MicrosoftAuth2Adapter)