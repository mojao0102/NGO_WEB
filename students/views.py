# from django.http import HttpResponse

# reference from courses app folder

from administration.func import app_func as admin_app_func
from django.shortcuts import render, get_list_or_404, get_object_or_404

# @admin_app_func.staff_access_control
def student_list(request):
    return render(request, "students/student_list.html")

# @admin_app_func.staff_access_control
def student_create(request):
    return render(request, "students/student_edit.html")

# @admin_app_func.staff_access_control
def student_edit(request, student_id):
    return render(request, "student/student_edit.html")

# @admin_app_func.staff_access_control
def student_view(request, student_id):
    return render(request, "students/student_view.html")