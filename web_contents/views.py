# Create your views here.
from django.shortcuts import render, get_list_or_404, get_object_or_404
from .models import News

def news_list(request):
    news_list = News.objects.all().order_by('-publish_date')
    return render(request, "web_contents/news_list.html", {
        "news_list" : news_list
    })

def news_create(request):
    return render(request, "web_contents/news_edit.html")

def news_edit(request, news_id):
    return render(request, "web_contents/news_edit.html")

# def news_view(request, news_id):
#     return render(request, "news_view.html")