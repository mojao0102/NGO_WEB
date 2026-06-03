from django.urls import path
from . import views

app_name = 'front_web'

urlpatterns = [
    path('', views.home, name='home'),
    path('about', views.about, name='about'),

    path('newses', views.newses, name='newses'),
    path('newses/<int:news_id>', views.news, name='news'),

    path('login', views.student_login, name='student_login'),
    path('logout', views.student_logout, name='student_logout'),
    path('register', views.student_register, name='student_register'),

    path('course_list/<int:mc_id>', views.course_list, name='course_list'),
    path('course/<int:course_id>', views.course, name='course'),

    path('course/<int:course_id>/pay', views.course_payment, name='course_payment'),
    path('payment_successful', views.payment_successful, name='payment_successful'),
    path('payment_fail', views.payment_fail, name='payment_fail'),

    path('dashboard', views.student_dashboard, name='student_dashboard'),
]
