from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='couse_list'),
    path('course', views.course, name='course'),
]