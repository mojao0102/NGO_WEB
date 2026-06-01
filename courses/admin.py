from django.contrib import admin
from administration.helper_funcs import ModelAdminOverride
from .models import CourseMainCategory, CourseSubCategory, Course, CourseTemplate, CourseSchedule

@admin.register(CourseMainCategory)
class CourseMainCategoryAdmin(ModelAdminOverride):
    list_display = ('name', 'created_datetime')
    search_fields = ('name',)

@admin.register(CourseSubCategory)
class CourseSubCategoryAdmin(ModelAdminOverride):
    list_display = ('name', 'main_category__name', 'created_datetime')
    search_fields = ('name', 'main_category__name')


@admin.register(CourseTemplate)
class CourseTemplateAdmin(ModelAdminOverride):
    list_display = ('name', 'sub_category__name', 'created_datetime')
    search_fields = ('name', 'sub_category__name')

@admin.register(Course)
class CourseAdmin(ModelAdminOverride):
    list_display = ('name', 'code', 'course_status', 'created_datetime')
    search_fields = ('name', 'code')

@admin.register(CourseSchedule)
class CourseScheduleAdmin(ModelAdminOverride):
    list_display = ('course__code', 'course__name', 'day_of_week', 'created_datetime')
    search_fields = ('course__code','course__name')

