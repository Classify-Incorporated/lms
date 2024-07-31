from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout

def login(request):
    return render(request, 'accounts/login.html')

def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def student(request):
    return render(request, 'accounts/student.html')

def activity_stream(request):
    return render(request, 'accounts/activity_stream.html')

def courses(request):
    return render(request, 'accounts/courses.html')

def calendar(request):
    return render(request, 'accounts/calendar.html')

def messages(request):
    return render(request, 'accounts/messages.html')

def grades(request):
    return render(request, 'accounts/grades.html')

def assist(request):
    return render(request, 'accounts/assist.html')

def tools(request):
    return render(request, 'accounts/tools.html')

def sign_out(request):
    auth_logout(request)
    return redirect('accounts/login')