from functools import wraps
from django.utils import timezone
from django.db.models import Q, F, Count, Case, When, Value, CharField
from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.http import HttpResponse, Http404
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


#=======================Home=======================#
@load_main_category
def home(request):

    current_time = timezone.localtime(timezone.now())
    
    #load newses
    list_news = News.objects.filter(is_publish = True, expiry_date__gt=current_time).order_by("-publish_date", "-created_datetime")[:3]
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

#=======================About=======================#
@load_main_category
def about(request):
    list_center = get_list_or_404(Center)
    context = {'list_center': list_center, 'list_mc' : request.list_mc}
    return render(request, "about.html", context)

#=======================News=======================#
@load_main_category
def newses(request):
    current_time = timezone.localtime(timezone.now())
    #load newses
    list_news = News.objects.filter(is_publish = True, expiry_date__gt=current_time).order_by("-publish_date", "-created_datetime")
    context = {'list_mc' : request.list_mc, "list_news" : list_news}
    return render(request, "news.html", context)

@load_main_category
def news(request, news_id):
    #Get news object
    obj_news = get_object_or_404(News, id = news_id)
    context = {'list_mc' : request.list_mc, "obj_news" : obj_news}
    return render(request, "news_blog.html", context)

#=======================Course=======================#
@load_main_category
def course_list(request, mc_id):



    
    context = {'list_mc' : request.list_mc}
    return render(request, "course_list.html", context)

@load_main_category
def course(request, course_id):
    
    if request.method == "GET":
        #Get course object
        #Build custom field at course queryset
        #Count valid signup
        course_queryset = Course.objects.annotate(
        valid_signup_count=Count(
            'signup_set', 
            filter=~Q(signup_set__payment_ref="") & Q(signup_set__is_reject=False))
        ).annotate(
        #generate str_course_status base on valid_signup_count
            str_course_status=Case(
            When(
                max_no_student__gt=0, 
                valid_signup_count__gte=F('max_no_student'), 
                then=Value('full')
            ),
            default=Value('available'),
            output_field=CharField(),))
        
        #Only course with status "created", web published and not over registation expiry date allow to show
        obj_course = get_object_or_404(course_queryset, id = course_id, 
                                    is_web_publish = True, 
                                    registation_expiry_date__gt=timezone.localtime(timezone.now()),
                                    course_status = "created")
        #End get course object

        context = {'list_mc' : request.list_mc, "obj_course" : obj_course}

        return render(request, "course.html", context)
    
    else:
        return render(request, "course.html", context)
    
#=======================Login/Register=======================#
@load_main_category
def student_login(request):
    #switch to dashbroad when login success
    context = {'list_mc' : request.list_mc}
    return render(request, "member_login.html", context)

@load_main_category
def student_register(request):

    #switch to login when register success
    context = {'list_mc' : request.list_mc}
    return render(request, "member_register.html", context)
