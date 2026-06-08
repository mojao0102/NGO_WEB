from django.urls import path
from . import views

app_name = 'administration'

urlpatterns = [
    path('login/', views.staff_login, name='staff_login'),
    path('logout/', views.staff_logout, name='staff_logout'),
    path('', views.dashboard, name='dashboard'),
    path('course-template/', views.course_template, name='course_template'),
    path('course-template/create/', views.course_template_create, name='course_template_create'),
    path('course/', views.course, name='course'),
    path('course/list/', views.course_list, name='course_list'),
    path('course/create/', views.course_create, name='course_create'),
    path('news/', views.news, name='news'),
    path('news/create/', views.news_create, name='news_create'),
    path('news/<int:pk>/edit/', views.news_edit, name='news_edit'),
    path('student/', views.student, name='student'),
    path('student/create/', views.student_create, name='student_create'),
    path('teacher/', views.teacher, name='teacher'),
    path('teacher/create/', views.teacher_create, name='teacher_create'),
]
