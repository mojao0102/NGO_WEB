from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('list/', views.course_list, name='course_list'),
    path('create/', views.course_create, name='course_create'),
    path('edit/<int:course_id>', views.course_edit, name='course_edit'),
    path('view/<int:course_id>', views.course_view, name='course_view'),
]