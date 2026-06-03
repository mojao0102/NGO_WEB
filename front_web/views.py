from django.utils import timezone
from django.db import transaction
from django.db.models import Q, F, Count, Case, When, Value, CharField, ExpressionWrapper, DateTimeField
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import send_mail
from administration.models import Center
from courses.models import CourseMainCategory, CourseSubCategory, Course, SignUp
from students.models import Student
from students.func import app_func as student_app_func
from web_contents.models import News
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from functools import wraps
import stripe
from .func import app_func as frontweb_app_func, stripe_func

# region View: Home/About
@frontweb_app_func.load_main_category
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

@frontweb_app_func.load_main_category
def about(request):
    list_center = get_list_or_404(Center)
    context = {'list_center': list_center, 'list_mc' : request.list_mc}
    return render(request, "about.html", context)
# endregion

# region View: News
@frontweb_app_func.load_main_category
def newses(request):
    current_time = timezone.localtime(timezone.now())
    #load newses
    list_news = News.objects.filter(is_publish = True, expiry_date__gt=current_time).order_by("-publish_date", "-created_datetime")
    context = {'list_mc' : request.list_mc, "list_news" : list_news}
    return render(request, "news.html", context)

@frontweb_app_func.load_main_category
def news(request, news_id):
    #Get news object
    obj_news = get_object_or_404(News, id = news_id)
    context = {'list_mc' : request.list_mc, "obj_news" : obj_news}
    return render(request, "news_blog.html", context)
# endregion

# region View: Register/Email Verification/Login/LogOut
@frontweb_app_func.load_main_category
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
        new_student = Student(student_no=student_app_func.generate_unique_student_number(),
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


@frontweb_app_func.load_main_category
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
            request.session['student_name'] = student.cn_name

            messages.success(request, f"歡迎回來，{student.username}")

            return redirect("front_web:home")
        else:
            messages.error(request, "帳號或密碼錯誤，請重新輸入")        
            context = {'list_mc': request.list_mc, 'input_data': request.POST}
            return render(request, "student_login.html", context)
    else:#Get
        context = {'list_mc' : request.list_mc}
        return render(request, "student_login.html", context)
    
@frontweb_app_func.load_main_category
def student_logout(request):

    if request.method == "POST":
        if 'student_id' in request.session:
            del request.session['student_id']

        if 'student_username' in request.session:
            del request.session['student_username']
        
        messages.success(request, "你已成功登出")
        return redirect("front_web:student_login")
    
    return render(request, "home.html")
# endregion

# region View: Course/Category
@frontweb_app_func.load_main_category
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

@frontweb_app_func.load_main_category
def course(request, course_id):
    
    if request.method == "POST":
        print("POST here")
    else:#GET
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
# endregion

# region View: Course SignUp/Payment
def course_payment(request, course_id):
    if request.method == "POST":
        #1. Get course and check if course still avaliable, Only course with status "created", web published and not over registation expiry date allow to sign_up
        course_queryset = Course.objects.annotate(
        valid_signup_count=Count('signup_set', filter=~Q(signup_set__payment_ref="") & Q(signup_set__is_reject=False)))      
        obj_course = course_queryset.filter(id = course_id, is_web_publish = True, registation_expiry_date__gt=timezone.localtime(timezone.now()), course_status = "created").first()
        if not obj_course:
            messages.error(request, "課程狀態已更改，請刷新頁面")
            return redirect('front_web:course', course_id=course_id)
        #2. Check if student login already
        if not request.session.get('student_id'):
            messages.error(request, "請先登入再報名")
            return redirect('front_web:course', course_id=course_id)  
        #3. Check if student signup already
        if SignUp.objects.filter(course_id=obj_course.id, student_id=request.session['student_id']):
            messages.error(request, "您已報名參加此課程")
            return redirect('front_web:course', course_id=course_id)

        if not settings.STRIPE_SECRET_KEY:
            messages.error(request, "付款系統尚未設定，請聯絡本中心")
            return redirect('front_web:course', course_id=course_id)

        student = get_object_or_404(Student, id=request.session['student_id'])
        
        # stripe progress
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe.api_version = settings.STRIPE_API_VERSION

            session = stripe.checkout.Session.create(
                line_items=[{
                    'price_data': {
                        'currency': settings.STRIPE_CURRENCY,
                        'product_data': {'name': f"{obj_course.name}-{obj_course.code}"},
                        'unit_amount': stripe_func._money_to_stripe_amount(obj_course.course_fee),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                customer_email=student.email,
                client_reference_id=f"course:{obj_course.id}:student:{student.id}",
                metadata={
                    'course_id': str(obj_course.id),
                    'student_id': str(student.id),
                },
                success_url=request.build_absolute_uri(reverse('front_web:payment_successful')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('front_web:payment_fail')) + f'?course_id={obj_course.id}',
            )
        except stripe.error.StripeError:
            messages.error(request, "未能建立付款連結，請稍後再試")
            return redirect('front_web:course', course_id=course_id)

        return redirect(session.url, code=303)
    else:
        return render(request, "payment_fail.html", {"course_id" : course_id})

@frontweb_app_func.load_main_category
def payment_successful(request):
    # 1. 從網址列（GET 請求）撈出 Stripe 帶回來的 session_id
    session_id = request.GET.get('session_id')
    
    if not session_id:
        # 如果使用者試圖直接輸入網址偷跑進來，直接踢走！
        messages.error(request, "不合法的請求，請循正常管道付款")
        return redirect("front_web:home")
        
    try:
        # 2. 向 Stripe 總部對帳，撈出這筆交易的完整後端資料
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.api_version = settings.STRIPE_API_VERSION
        session = stripe.checkout.Session.retrieve(session_id)
        
        # 3. 嚴格檢查付款狀態是否真的為 "paid"
        if session.payment_status == "paid":
            
            signup, is_new_record = stripe_func._create_signup_from_checkout_session(session)
            course = signup.course
            student = signup.student
                
            # 6. 把課程與付款資訊傳給前端網頁，做個漂亮的感謝收據
            context = {
                'course_id' : course.id,
                'course_list_id': course.sub_category.main_category_id,
                'course_name': course.name,
                'course_code': course.code,
                'student_name': student.cn_name,
                'student_no': student.student_no,
                'amount': signup.payment_amount,
                'payment_ref': signup.payment_ref,
                'payment_date': signup.payment_date,
                'is_new_record': is_new_record,
                'list_mc' : request.list_mc
            }
            return render(request, "payment_successful.html", context)
            
        else:
            messages.error(request, "付款尚未成功，請確認扣款狀態")
            return redirect("front_web:student_dashboard")
            
    except stripe.error.StripeError as e:
        # 萬一對帳失敗（例如黑客自己隨便編造假的 session_id 網址）
        messages.error(request, "無效的交易代碼")
        return redirect("front_web:home")
    except (Course.DoesNotExist, Student.DoesNotExist, ValueError):
        messages.error(request, "未能確認付款資料，請聯絡本中心")
        return redirect("front_web:home")


@csrf_exempt
def stripe_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    if not webhook_secret:
        return HttpResponse(status=400)

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.api_version = settings.STRIPE_API_VERSION

        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event["type"] in ["checkout.session.completed", "checkout.session.async_payment_succeeded"]:
        session = event["data"]["object"]
        if session.get("payment_status") == "paid":
            try:
                stripe_func._create_signup_from_checkout_session(session)
            except (Course.DoesNotExist, Student.DoesNotExist, ValueError):
                return HttpResponse(status=400)

    return HttpResponse(status=200)

@frontweb_app_func.load_main_category
def payment_fail(request):
    course_id = request.GET.get('course_id')
    context = {'list_mc' : request.list_mc, "course_id" : course_id}
    return render(request, "payment_fail.html", context)
# endregion

# region View: Dashboard
@frontweb_app_func.load_main_category
def student_dashboard(request):

    #Check if login
    if not request.session.get('student_id'):
        messages.error(request, "請先登入")
        return redirect('front_web:student_login')  

    list_mode = "PastCourse" if request.GET.get("ListMode") == "PastCourse" else "CurrentCourse"

    context = {'list_mc' : request.list_mc, "list_mode" : list_mode}

    if list_mode == "CurrentCourse":
        print("Get current course")
        context["list_course"] = Course.objects.annotate(course_end_datetime=ExpressionWrapper(F('period_to') + F('time_to'), output_field=DateTimeField())
        ).filter(signup_set__student_id=request.session.get('student_id'), 
                                            signup_set__is_reject=False,
                                            course_end_datetime__gte=timezone.localtime(timezone.now()),
                                            course_status='created')
    else:
        print("Get past courses")
        context["list_course"] = Course.objects.annotate(course_end_datetime=ExpressionWrapper(F('period_to') + F('time_to'), output_field=DateTimeField())
        ).filter(signup_set__student_id=request.session.get('student_id'), 
                                            signup_set__is_reject=False,
                                            course_end_datetime__lte=timezone.localtime(timezone.now()),
                                            course_status='created')
    return render(request, "student_dashboard.html", context)
# endregion

