from django.urls import path
from . import views

app_name = 'web_contents'

urlpatterns = [
    path('list/', views.news_list, name='news_list'),
    path('create/', views.news_create, name='news_create'),
    path('edit/<int:news_id>', views.news_edit, name='news_edit'),
    # path('view/<int:news_id>', views.news_view, name='news_view'),
]