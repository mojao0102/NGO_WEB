from administration.func import app_func as admin_app_func
from .models import Course
from django.db.models import Q, F
from django.shortcuts import render, redirect
from .func import app_func as course_app_func

@admin_app_func.staff_access_control
def course_list(request):
    
    

    list_course = course_app_func.get_courses_with_dynamic_status()
    context = {"list_course" : list_course}

    return render(request, "courses/course_list.html", context)

@admin_app_func.staff_access_control
def course_create(request):
    return render(request, "courses/course_edit.html")

@admin_app_func.staff_access_control
def course_edit(request, course_id):
    return render(request, "courses/course_edit.html")

@admin_app_func.staff_access_control
def course_view(request, course_id):
    return render(request, "courses/course_view.html")