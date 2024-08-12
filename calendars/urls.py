from django.urls import path
from .views import (calendars)

urlpatterns = [
    path('calendar/', calendars, name='calendar'),

]
