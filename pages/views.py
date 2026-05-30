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