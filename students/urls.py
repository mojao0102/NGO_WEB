from django.urls import path
from . import views

# From config/url.py 
# path('manage/students/', include('students.urls', namespace='students')),

app_name = 'students'

urlpatterns = [
    path('list/', views.student_list, name='student_list'),
    path('create/', views.student_create, name='student_create'),
    path('edit/<int:student_id>/', views.student_edit, name='student_edit'),
    path('view/<int:student_id>/', views.student_view, name='student_view'),
    ]