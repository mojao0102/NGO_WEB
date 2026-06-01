from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.home, name='home'),
    path('about', views.about, name='about'),

    path('newses', views.newses, name='newses'),
    path('newses/<int:news_id>', views.news, name='news'),

    path('login', views.student_login, name='student_login'),
    path('register', views.student_register, name='student_register'),

    path('course_list/<int:mc_id>', views.course_list, name='course_list'),
    path('course/<int:course_id>', views.course, name='course')
]
