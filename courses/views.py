from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.http import HttpResponse
# from courses.models import Courses


# Create your views here.
def course_list(request):
    return render(request, "courses.html")

def course(request):
    return render(request, "course.html")