from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('list/', views.teacher_list, name='teacher_list'),
    path('create/', views.teacher_create, name='teacher_create'),
    path('view/<int:teacher_id>', views.teacher_view, name='teacher_view'),
    path('edit/<int:teacher_id>', views.teacher_edit, name='teacher_edit'),
]
