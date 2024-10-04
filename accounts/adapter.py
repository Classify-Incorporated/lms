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
from allauth.socialaccount.models import SocialToken, SocialAccount

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
        print("Entering pre_social_login")
        email = sociallogin.account.extra_data.get('mail', sociallogin.account.extra_data.get('userPrincipalName', ''))
        print(f"User Email: {email}")
        print(f"Social Login Data: {sociallogin.account.extra_data}")

        try:
            # Check if the user exists by email
            user = CustomUser.objects.get(email=email)
            print(f"Found existing user: {user.email}")

            # Assign the existing user to the sociallogin object
            sociallogin.state['process'] = 'login'
            sociallogin.user = user
            user.backend = 'allauth.account.auth_backends.AuthenticationBackend'
            
            # Check if the social account exists, if not, create and link it
            social_account, created = SocialAccount.objects.get_or_create(
                user=user, 
                provider=sociallogin.account.provider, 
                uid=sociallogin.account.uid, 
                defaults={'extra_data': sociallogin.account.extra_data}
            )
            print(f"Linked Social Account: {social_account}")
            
            login(request, user)
            print("User logged in with existing account.")
            raise ImmediateHttpResponse(redirect('dashboard'))
        except CustomUser.DoesNotExist:
            print("User does not exist.")
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

    authorize_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
    access_token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    profile_url = "https://graph.microsoft.com/v1.0/me"

    def complete_login(self, request, app, token, **kwargs):
        headers = {'Authorization': f'Bearer {token.token}'}
        print(f"Starting complete_login. Token: {token.token}")

        try:
            # Fetch the user's profile information
            resp = requests.get(self.profile_url, headers=headers)
            resp.raise_for_status()
            extra_data = resp.json()

            print(f"Profile response from Microsoft: {extra_data}")

            # Create or retrieve the social account
            social_login = self.get_provider().sociallogin_from_response(request, extra_data)
            account = social_login.account

            if request.user.is_authenticated:
                print(f"User is authenticated: {request.user}")
                account.user = request.user
                account.save()

            else:
                print("User is not authenticated.")
            
            social_token, created = SocialToken.objects.get_or_create(
                account=account, 
                defaults={'token': token.token, 'expires_at': token.expires_at}
            )
            if not created:
                print("Social token already exists, updating it.")
                # Update the token if it already exists
                social_token.token = token.token
                social_token.expires_at = token.expires_at
                social_token.save()
                print(f"Updated SocialToken: {social_token.token}, Expires at: {social_token.expires_at}")
            else:
                print(f"New SocialToken created: {social_token.token}, Expires at: {social_token.expires_at}")

            return social_login
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred during profile request: {http_err}")
        except Exception as err:
            print(f"Error occurred during complete_login: {err}")


oauth2_login = OAuth2LoginView.adapter_view(MicrosoftAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(MicrosoftAuth2Adapter)