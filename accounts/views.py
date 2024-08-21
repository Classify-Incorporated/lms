from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as auth_logout, authenticate, login
from .forms import CustomLoginForm, profileForm
from .models import CustomUser, Profile
from django.contrib.auth.decorators import login_required


def admin_login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Authenticate the user
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                return render(request, 'accounts/login.html', {'form': form, 'error': 'Invalid email or password'})
        else:
            return render(request, 'accounts/login.html', {'form': form, 'error': 'Form data is not valid'})
    else:
        form = CustomLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

#List Profile
@login_required
def student(request):
    profiles = Profile.objects.filter(role__name__iexact='student')
    return render(request, 'accounts/student.html', {'profiles': profiles})

#View Profile
@login_required
def viewProfile(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    return render(request, 'accounts/viewStudentProfile.html',{'profile': profile})

#Modify Profile
@login_required
def updateProfile(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    if request.method == 'POST':
        form = profileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('student')
    else:
        form = profileForm(instance=profile)
    return render(request, 'accounts/updateStudentProfile.html', {'form': form,'profile': profile})


#Activate Profile
@login_required
def activateProfile(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    profile.active = True
    profile.save()
    return redirect('viewProfile', pk=profile.pk)

#Deactivate Profile
@login_required
def deactivateProfile(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    profile.active = False
    profile.save()
    return redirect('viewProfile', pk=profile.pk)

@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def activity_stream(request):
    return render(request, 'accounts/activity_stream.html')


def assist(request):
    return render(request, 'accounts/assist.html')

def tools(request):
    return render(request, 'accounts/tools.html')

def createProfile(request):
    return render(request, 'accounts/createStudentProfile.html')

def sign_out(request):
    auth_logout(request)
    return redirect('admin_login_view')
