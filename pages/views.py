from functools import wraps
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.http import HttpResponse
from administration.models import Center
from courses.models import CourseMainCategory, Course
from web_contents.models import News

#Decorator for load main category for nav bar
def load_main_category(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        request.list_mc = CourseMainCategory.objects.filter(is_active=True)      
        return view_func(request, *args, **kwargs)
    return _wrapped_view



#=======================View start here=======================#
@load_main_category
def home(request):

    current_time = timezone.localtime(timezone.now())
    #load newses
    list_news = News.objects.filter(is_publish = True, expiry_date__gt=current_time)
    #load course
    list_promote_course = Course.objects.filter(is_web_publish = True, 
                                        is_promote = True, 
                                        registation_expiry_date__gt=current_time, 
                                        course_status = 'created')
    context = {
        'list_mc' : request.list_mc, 
        'list_news' : list_news, 
        'list_promote_course' : list_promote_course}  
    
    print(request.user)

    return render(request, "home.html", context)

@load_main_category
def about(request):
    list_center = get_list_or_404(Center)
    context = {'list_center': list_center, 'list_mc' : request.list_mc}
    return render(request, "about.html", context)

@load_main_category
def newses(request):
    context = {'list_mc' : request.list_mc}
    return render(request, "news.html", context)

@load_main_category
def news(request, news_id):
    context = {'list_mc' : request.list_mc}
    return render(request, "news_blog.html", context)

@load_main_category
def student_login(request):
    context = {'list_mc' : request.list_mc}
    return render(request, "member_login.html", context)

@load_main_category
def student_register(request):
    context = {'list_mc' : request.list_mc}
    return render(request, "member_register.html", context)

@load_main_category
def course_list(request, mc_id):
    context = {'list_mc' : request.list_mc}
    return render(request, "course_list.html", context)

@load_main_category
def course(request, course_id):
    context = {'list_mc' : request.list_mc}
    return render(request, "course.html", context)
