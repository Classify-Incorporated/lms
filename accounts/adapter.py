from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from .models import Profile

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

        print(f'Extra data received from Microsoft: {extra_data}')

        user.email = extra_data.get('mail', extra_data.get('userPrincipalName', ''))
        user.first_name = extra_data.get('givenName', '')
        user.last_name = extra_data.get('surname', '')
        user.username = user.email  # Ensure username is set to the email

        # Do not set any password for social login users
        user.set_unusable_password()

        print(f'User populated with email: {user.email}, first_name: {user.first_name}, last_name: {user.last_name}')

        return user

    def save_user(self, request, sociallogin, form=None):
        user = sociallogin.user

        # Ensure the user is saved with the provided information
        user.save()
        print(f'User saved with email: {user.email}, first_name: {user.first_name}, last_name: {user.last_name}')

        # Ensure the profile is created or updated
        profile, created = Profile.objects.get_or_create(user=user)
        profile.first_name = user.first_name
        profile.last_name = user.last_name
        profile.save()
        print(f'Profile saved with first name: {profile.first_name}, last name: {profile.last_name}')

        return user
