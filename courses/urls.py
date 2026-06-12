from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('template/', views.course_template_list, name='course_template_list'),
    path('template/create/', views.course_template_create, name='course_template_create'),
    path('template/edit/<int:template_id>/', views.course_template_edit, name='course_template_edit'),
    path('list/', views.course_list, name='course_list'),
    path('create/', views.course_create, name='course_create'),
    # path('edit/<int:course_id>', views.course_edit, name='course_edit'),
    # path('delete/<int:course_id>', views.course_delete, name='course_delete'),
    # path('view/<int:course_id>', views.course_view, name='course_view'),
    path('edit/<str:hash_course>/', views.course_edit, name='course_edit'),
    # path('delete/<str:hash_course>', views.course_delete, name='course_delete'),
    path('view/<str:hash_course>/', views.course_view, name='course_view'),
]