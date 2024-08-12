from django.shortcuts import render

def calendars(request):
    return render(request, 'calendar/calendar.html')