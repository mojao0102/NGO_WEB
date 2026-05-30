from django.contrib import admin
from administration.helper_funcs import ModelAdminOverride
from .models import CourseMainCategory, CourseSubCategory

@admin.register(CourseMainCategory)
class CourseMainCategoryAdmin(ModelAdminOverride):
    list_display = ('name', 'created_datetime')
    search_fields = ('name',)

@admin.register(CourseSubCategory)
class CourseSubCategoryAdmin(ModelAdminOverride):
    list_display = ('name', 'main_category', 'created_datetime')
    search_fields = ('name', 'main_category')


