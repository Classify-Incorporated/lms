from django.urls import path
from .views import (calendars, activity_api)

urlpatterns = [
    path('calendars/', calendars, name='calendars'),
    path('api/activities/', activity_api, name='activity_api'),

]
