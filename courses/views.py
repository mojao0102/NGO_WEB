from django.shortcuts import render, get_list_or_404, get_object_or_404

def course_list(request):
    return render(request, "course_list.html")

def course_create(request):
    return render(request, "course_edit.html")

def course_edit(request, course_id):
    return render(request, "course_edit.html")

def course_view(request, course_id):
    return render(request, "course_view.html")