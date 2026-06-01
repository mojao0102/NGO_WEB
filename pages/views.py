from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.http import HttpResponse
from administration.models import Center


# Create your views here.
def home(request):
    return render(request, "home.html")

def about(request):
    list_center = get_list_or_404(Center)
    context = {'list_center': list_center}
    return render(request, "about.html", context)

def newses(request):
    return render(request, "news.html")

def news(request):
    return render(request, "news_blog.html")

def student_login(request):
    return render(request, "member_login.html")

def student_register(request):
    return render(request, "member_register.html")