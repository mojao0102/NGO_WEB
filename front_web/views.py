from functools import wraps
from django.utils import timezone
from django.db.models import Q, F, Count, Case, When, Value, CharField
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http import HttpResponse, Http404
from django.contrib import messages
from administration.models import Center
from courses.models import CourseMainCategory, CourseSubCategory, Course
from students.models import Student
from students import app_func
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

    #Get main category object by id & is_active
    obj_mc = get_object_or_404(CourseMainCategory, id = mc_id, is_active = True)

    #Get sub category list by mc_id & is_active
    list_sc = CourseSubCategory.objects.filter(main_category_id = mc_id, is_active = True).order_by("-name")

    context = {'list_mc' : request.list_mc, 
                "obj_mc" : obj_mc, 
                "list_sc" : list_sc}

    #check if is from sc button press at web page or page/mc button load
    sc_id = int(request.GET['sc'] if 'sc' in request.GET else list_sc[0].id if list_sc else 0)

    #Get sub category object
    if sc_id > 0 :

        context["obj_sc"] = get_object_or_404(CourseSubCategory, id = sc_id, is_active = True)

        #Get course list
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
                then=Value('名額已滿')
            ),
            default=Value('收生中'),
            output_field=CharField(),))
        
        #Only course with status "created", web published and not over registation expiry date allow to show
        context["list_course"] = course_queryset.filter(sub_category_id = sc_id, 
                                                is_web_publish = True, 
                                                registation_expiry_date__gt=timezone.localtime(timezone.now()),
                                                course_status = "created")
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
                then=Value('名額已滿')
            ),
            default=Value('收生中'),
            output_field=CharField(),))
        
        #Only course with status "created", web published and not over registation expiry date allow to show
        obj_course = get_object_or_404(course_queryset, id = course_id, 
                                    is_web_publish = True, 
                                    registation_expiry_date__gt=timezone.localtime(timezone.now()),
                                    course_status = "created")

        context = {'list_mc' : request.list_mc, "obj_course" : obj_course}

        return render(request, "course.html", context)
    
    else:
        return render(request, "course.html", context)
    
#=======================Register/Login/LogOut=======================#
@load_main_category
def student_register(request):

    if request.method == "POST":
        #Load data from POST
        username = request.POST['username']
        password = request.POST['password']
        password2 = request.POST['confirm_password']

        cn_name = request.POST['studentNameCh']
        en_name = request.POST['studentNameEn']
        dob = request.POST['studentDob']
        email = request.POST['contactEmail']
        school = request.POST['school']

        contact1Name = request.POST['contact1Name']
        contact1Phone = request.POST['contact1Phone']
        contact1Relation = request.POST['contact1Relation']

        contact2Name = request.POST['contact2Name']
        contact2Phone = request.POST['contact2Phone']
        contact2Relation = request.POST['contact2Relation']
        
        #Error Checking
        blnInputError = False

        if password != password2:
            messages.error(request, "密碼不匹配")
            blnInputError = True          
        elif Student.objects.filter(username=username).exists():
            messages.error(request, "帳號已存在")
            blnInputError = True          
        elif Student.objects.filter(email=email.lower()).exists():
            messages.error(request, "Email已被使用")
            blnInputError = True

        if blnInputError:
            context = {'list_mc' : request.list_mc, "input_data" : request.POST}
            return render(request, "student_register.html", context)

        #Create student
        current_time = timezone.localtime(timezone.now())
        new_student = Student(student_no=app_func.generate_unique_student_number(),
                            cn_name=cn_name,
                            en_name=en_name,
                            dob=dob,
                            email=email,
                            contact1_name=contact1Name,
                            contact1_relationship=contact1Relation,
                            contact1_phone=contact1Phone,
                            contact2_name=contact2Name,
                            contact2_relationship=contact2Relation,
                            contact2_phone=contact2Phone,
                            username=username,
                            password=password,
                            is_active=True,
                            register_date=current_time,
                            file_status="created",
                            created_by="web registation",
                            created_datetime=current_time,
                            last_updated_by="web registation",
                            last_updated_datetime=current_time)
        new_student.save()
        messages.success(request, "註冊成功")
        return redirect("front_web:student_login")
    
    else: #From GET
        context = {'list_mc' : request.list_mc}
        return render(request, "student_register.html", context)


@load_main_category
def student_login(request):

    if request.method == "POST":
    #Load data from POST
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        student = Student.objects.filter(username=username, password=password).first()

        if student:
            if not student.is_active:
                messages.error(request, "該帳號已被停用，請聯絡本中心")
                context = {'list_mc': request.list_mc, 'input_data': request.POST}
                return render(request, "student_login.html", context)
            
            request.session['student_id'] = student.id
            request.session['student_username'] = student.username

            messages.success(request, f"歡迎回來，{student.username}")

            return redirect("front_web:home")
        else:
            messages.error(request, "帳號或密碼錯誤，請重新輸入")        
            context = {'list_mc': request.list_mc, 'input_data': request.POST}
            return render(request, "student_login.html", context)
    else:#Get
        context = {'list_mc' : request.list_mc}
        return render(request, "student_login.html", context)
    
@load_main_category
def student_logout(request):

    if request.method == "POST":
        if 'student_id' in request.session:
            del request.session['student_id']

        if 'student_username' in request.session:
            del request.session['student_username']
        
        messages.success(request, "你已成功登出")
        return redirect("front_web:student_login")
    
    return render(request, "home.html")

