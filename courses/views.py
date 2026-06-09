from administration.func import app_func as admin_app_func

from django.shortcuts import render

@admin_app_func.staff_access_control
def course_list(request):
    return render(request, "courses/course_list.html")

@admin_app_func.staff_access_control
def course_create(request):
    return render(request, "courses/course_edit.html")

@admin_app_func.staff_access_control
def course_edit(request, course_id):
    return render(request, "courses/course_edit.html")

@admin_app_func.staff_access_control
def course_view(request, course_id):
    return render(request, "courses/ourse_view.html")