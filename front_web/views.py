from django.utils import timezone
from django.db.models import Q, F, Count, Case, When, Value, CharField, ExpressionWrapper, DateTimeField
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from administration.models import Center
from courses.models import CourseMainCategory, CourseSubCategory, Course, SignUp, SignUpRefund
from students.models import Student
from students.func import app_func as student_app_func
from web_contents.models import News
from .func import app_func as frontweb_app_func, stripe_func
from courses.func import app_func as courses_app_func

import stripe

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

# region View: Register/EmailVerification/Login/LogOut
@frontweb_app_func.load_main_category
def student_register(request):

    if request.method == "POST":
        #Load data from POST
        username = request.POST['username']
        password = request.POST.get("password", "")
        password2 = request.POST.get("confirm_password", "")

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

        if not password or len(password) < 6:
            messages.error(request, "密碼長度至少需要6個字元以上")
            blnInputError = True                
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
        obj_new_student = Student(student_no=student_app_func.generate_unique_student_number(),
                            cn_name=cn_name,
                            en_name=en_name,
                            dob=dob,
                            email=email,
                            #For email verification
                            is_email_verified=False,
                            contact1_name=contact1Name,
                            contact1_relationship=contact1Relation,
                            contact1_phone=contact1Phone,
                            contact2_name=contact2Name,
                            contact2_relationship=contact2Relation,
                            contact2_phone=contact2Phone,
                            school=school,
                            username=username,
                            password=password,
                            is_active=True,
                            register_date=current_time,
                            created_by="web registation",
                            last_updated_by="web registation",)
        obj_new_student.save()

        #default as logged in
        frontweb_app_func.create_login_session(request, obj_new_student)

        #Make sure last_login up to date
        obj_new_student.refresh_from_db()

        try:
            frontweb_app_func.send_student_security_email(request, obj_new_student, "activation")
        except Exception:
            messages.warning(request, "帳號已建立，但驗證信發送失敗，請聯絡中心管理員啟用帳號")
            return redirect("front_web:student_login")
        
        messages.success(request, "註冊成功，確認郵件已寄送至您的註冊信箱。請點擊郵件中的連結驗證您的郵箱地址")
        return redirect("front_web:student_register_pending")  
    
    else: #GET
        context = {'list_mc' : request.list_mc}
        return render(request, "student_register.html", context)

@frontweb_app_func.load_main_category
@frontweb_app_func.student_access_control(require_email_verification=False)
def student_register_pending(request):
    context = {"email": request.obj_student.email, "list_mc": request.list_mc}
    return render(request, "student_register_pending.html", context)

@frontweb_app_func.load_main_category
@frontweb_app_func.student_access_control(require_email_verification=False)
def student_change_email_and_resend(request):

    obj_student = request.obj_student

    if obj_student.is_email_verified:
        messages.info(request, "您的電子郵件此前已驗證成功，無需重複驗證")
        return redirect("front_web:student_dashboard")

    if request.method == "POST":
        new_email = request.POST.get('new_email', '').strip()
        
        if not new_email:
            messages.error(request, "電子郵件欄位不可為空")
            return render(request, "student_change_email.html", {"old_email": obj_student.email, "list_mc": request.list_mc})
            
        #Check if new email addr be used by other student
        if Student.objects.filter(email=new_email).exclude(id=obj_student.id).exists():
            messages.error(request, "此電子郵件已被其他帳號註冊，請更換其他郵件")
            return render(request, "student_change_email.html", {"old_email": obj_student.email, "list_mc": request.list_mc})
            
        obj_student.email = new_email
        obj_student.save()
        
        #Send verification
        try:
            #frontweb_app_func.send_verification_email(request, obj_student, "activation")
            frontweb_app_func.send_student_security_email(request, obj_student, "activation")
            messages.success(request, f"Email修改成功！全新的驗證信已成功寄送至：{new_email}")
        except Exception:
            messages.warning(request, "Email雖已修改，但新驗證信發送失敗，請聯絡中心管理員")
            
        #Switch to email pending
        return redirect("front_web:student_register_pending")
        
    #GET
    context={"old_email": obj_student.email, "list_mc": request.list_mc}
    return render(request, "student_change_email.html", context)

def student_verifiy_email(request, uidb64, token):
    #負責解密 uid 並檢查 Token 是否依然有效，有效則改為已驗證
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        obj_student = Student.objects.get(id=uid)
    except (TypeError, ValueError, OverflowError, Student.DoesNotExist):
        obj_student = None
    # 核心安全驗證：檢查 Token 是否合法、是否過期、對象資料是否變動過
    if obj_student is not None and frontweb_app_func.verify_activation_token(obj_student, token):
        obj_student.is_email_verified = True
        #Update last_login for killing the token
        obj_student.last_login = timezone.localtime(timezone.now())
        obj_student.save()
        messages.success(request, "您的電子信箱已成功驗證！現在可以正常登入系統了")
        return redirect('front_web:student_login')
    else:
        frontweb_app_func.clear_login_session(request)
        return HttpResponse("<h3>此啟用連結已失效或過期，請重新嘗試註冊或聯絡中心</h3>")

@frontweb_app_func.load_main_category
def student_login(request):

    if request.method == "POST":
    #Load data from POST
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        obj_student = Student.objects.filter(username=username, password=password).first()

        if obj_student:
            if not obj_student.is_active:
                frontweb_app_func.clear_login_session(request)
                messages.error(request, "帳號已被停權，請聯絡中心")
                return redirect("front_web:student_login")
            
            frontweb_app_func.create_login_session(request, obj_student)
            messages.success(request, f"歡迎回來，{obj_student.username}")
            return redirect("front_web:home")
        else:
            frontweb_app_func.clear_login_session(request)
            messages.error(request, "帳號或密碼錯誤，請重新輸入")        
            context = {'list_mc': request.list_mc, 'input_data': request.POST}
            return render(request, "student_login.html", context)
    else:#Get
        context = {'list_mc' : request.list_mc}
        return render(request, "student_login.html", context)
    
@frontweb_app_func.load_main_category
def student_logout(request):
    if request.method == "POST":
        frontweb_app_func.clear_login_session(request)      
        messages.success(request, "你已成功登出")
        return redirect("front_web:student_login")  
    return render(request, "home.html")

@frontweb_app_func.load_main_category
def student_forget_password(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()     
        obj_student = Student.objects.filter(email=email).first()
        if obj_student:
            #frontweb_app_func.send_password_reset_email(request, obj_student, "reset_password")
            frontweb_app_func.send_student_security_email(request, obj_student, "reset_password")
        messages.success(request, "重設驗證連結已成功寄出，請至您的電子信箱查收")
        return redirect("front_web:student_login")
    
    context = {'list_mc' : request.list_mc}
    return render(request, "student_forget_password.html", context)

@frontweb_app_func.load_main_category
def student_reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        obj_student = Student.objects.get(id=uid)
    except (TypeError, ValueError, OverflowError, Student.DoesNotExist):
        obj_student = None

    # 核心安全驗證：檢查 Token 是否有效
    if obj_student is not None and frontweb_app_func.verify_activation_token(obj_student, token):
        
        if request.method == "POST":
            password = request.POST.get("password", "")
            password_confirm = request.POST.get("confirm_password", "")
            
            if not password or len(password) < 6:
                messages.error(request, "密碼長度至少需要6個字元以上")
                return render(request, "student_reset_password.html", {"uidb64": uidb64, "token": token, 'list_mc' : request.list_mc})
                
            if password != password_confirm:
                messages.error(request, "密碼不匹配")
                return render(request, "student_reset_password.html", {"uidb64": uidb64, "token": token, 'list_mc' : request.list_mc})

            obj_student.password = password
            obj_student.save()
            
            frontweb_app_func.clear_login_session(request)          
            messages.success(request, "密碼已成功更新, 請使用新密碼進行登入")
            return redirect("front_web:student_login")
        
        return render(request, "student_reset_password.html", {"uidb64": uidb64, "token": token, 'list_mc' : request.list_mc})
    else:
        return HttpResponse("<h3>該密碼重設連結已失效、過期或已被使用, 請重新申請</h3>")
# endregion

# region Edit user info/Change password
@frontweb_app_func.load_main_category
@frontweb_app_func.student_access_control()
def student_edit_info(request):

    if request.method == "POST":
        cn_name = request.POST.get('studentNameCh')
        en_name = request.POST.get('studentNameEn')
        dob = request.POST.get('studentDob')
        school = request.POST.get('school')

        contact1Name = request.POST.get('contact1Name')
        contact1Phone = request.POST.get('contact1Phone')
        contact1Relation = request.POST.get('contact1Relation')

        contact2Name = request.POST.get('contact2Name')
        contact2Phone = request.POST.get('contact2Phone')
        contact2Relation = request.POST.get('contact2Relation')

        try:
            #Get student
            obj_student = Student.objects.get(id=request.session.get('student_id'))

            obj_student.cn_name=cn_name
            obj_student.en_name=en_name
            obj_student.dob=dob
            obj_student.school=school

            obj_student.contact1_name=contact1Name
            obj_student.contact1_relationship=contact1Relation
            obj_student.contact1_phone=contact1Phone

            obj_student.contact2_name=contact2Name
            obj_student.contact2_relationship=contact2Relation
            obj_student.contact2_phone=contact2Phone

            obj_student.last_updated_by=f"student_id:{obj_student.id}"

            obj_student.save()

            messages.success(request, "成功修改")
            return redirect("front_web:student_edit_info")

        except Exception as e:
            print(f"An error occurred: {e}")
            messages.error(request, "系統錯誤, 請聯絡中心管理員")
            context = {'list_mc' : request.list_mc, "student" : request.obj_student, "input_data" : request.POST}
            return render(request, "student_edit_info.html", context)   
    else:    
        context = {'list_mc' : request.list_mc, "student" : request.obj_student}
        return render(request, "student_edit_info.html", context)

@frontweb_app_func.load_main_category
@frontweb_app_func.student_access_control()
def student_change_password(request):   

    if request.method == "POST":
        old_password = request.POST.get('old_password', "")
        new_password = request.POST.get('new_password', "")
        confirm_new_password = request.POST.get('confirm_new_password', "")

        try:
            #GEt student
            obj_student = Student.objects.get(id=request.session.get('student_id'))

            #check input
            blnInputError = False
            if old_password != obj_student.password:
                messages.error(request, "目前密碼不正確")
                blnInputError = True  
            elif not new_password or len(new_password) < 6:
                messages.error(request, "新密碼長度至少需要6個字元以上")
                blnInputError = True                
            elif new_password != confirm_new_password:
                messages.error(request, "新密碼不匹配")
                blnInputError = True          

            if blnInputError:
                context = {'list_mc' : request.list_mc, "student" : request.obj_student}
                return render(request, "student_change_password.html", context)

            obj_student.password=new_password
            obj_student.last_updated_by=f"student_id:{obj_student.id}"
            obj_student.save()

            messages.success(request, "成功修改密碼")
            return redirect("front_web:student_change_password")

        except Exception as e:
            print(f"An error occurred: {e}")
            messages.error(request, "系統錯誤, 請聯絡中心管理員")
            context = {'list_mc' : request.list_mc, "student" : request.obj_student}
            return render(request, "student_change_password.html", context)   
    else:  
        context = {'list_mc' : request.list_mc, "student" : request.obj_student}
        return render(request, "student_change_password.html", context)
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
        valid_signup_count=Count('signup_set', filter=~Q(signup_set__payment_ref="") & Q(signup_set__sign_up_status="success") & Q(signup_set__cancel_date__isnull=True))
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
        valid_signup_count=Count('signup_set', filter=~Q(signup_set__payment_ref="") & Q(signup_set__sign_up_status="success") & Q(signup_set__cancel_date__isnull=True))
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
@frontweb_app_func.student_access_control()
def course_payment(request, course_id):
    if request.method == "POST":

        #1 Get course and check if course still avaliable, Only course with status "created", web published, signup number < max no and not over registation expiry date allow to sign_up
        course_queryset = Course.objects.annotate(
        valid_signup_count=Count('signup_set', filter=~Q(signup_set__payment_ref="") & Q(signup_set__sign_up_status="success") & Q(signup_set__cancel_date__isnull=True)))     
        obj_course = course_queryset.filter(id = course_id, is_web_publish = True, registation_expiry_date__gt=timezone.localtime(timezone.now()), course_status = "created").first()
        if not obj_course:
            messages.error(request, "課程狀態已更改，請刷新頁面")
            return redirect('front_web:course', course_id=course_id)
        
        #2. Check if student signup already
        if SignUp.objects.filter(course_id=obj_course.id, student_id=request.session['student_id'], sign_up_status="success", cancel_date__isnull=True):
            messages.error(request, "您已報名參加此課程")
            return redirect('front_web:course', course_id=course_id)

        #3. Check if stripe key define at setting
        if not settings.STRIPE_SECRET_KEY:
            messages.error(request, "付款系統出錯，請聯絡本中心")
            return redirect('front_web:course', course_id=course_id)
        
        # stripe progress
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe.api_version = settings.STRIPE_API_VERSION

            session = stripe.checkout.Session.create(
                line_items=[{
                    'price_data': {
                        'currency': settings.STRIPE_CURRENCY,
                        'product_data': {'name': f"{obj_course.name}-{obj_course.code}"},
                        'unit_amount': stripe_func.money_to_stripe_amount(obj_course.course_fee),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                customer_email=request.obj_student.email,
                client_reference_id=f"course:{obj_course.id}:student:{request.obj_student.id}",
                metadata={
                    'course_id': str(obj_course.id),
                    'student_id': str(request.obj_student.id),
                },
                success_url=request.build_absolute_uri(reverse('front_web:payment_successful')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('front_web:payment_fail')) + f'?course_id={obj_course.id}',)
            
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
            
            try:
                signup, is_new_record = stripe_func.create_signup_from_checkout_session(session)

                if is_new_record:
                    frontweb_app_func.send_signup_success_email(request, signup)

            except (Course.DoesNotExist, Student.DoesNotExist, ValueError):
                print("fail to create sign up")
                return HttpResponse(status=400)
            
            course = signup.course
            student = signup.student
                
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

    print("in webhook now")

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
                stripe_func.create_signup_from_checkout_session(session)
            except (Course.DoesNotExist, Student.DoesNotExist, ValueError):
                return HttpResponse(status=400)
    #Refund handling(enable later if needed)
    # elif event["type"] == "charge.refunded":
    #     charge = event["data"]["object"]
    #     payment_intent_id = charge.get("payment_intent")
    #     refund_amount = Decimal(charge.get("amount_refunded", 0)) / Decimal("100")
        
    #     refunds = charge.get("refunds", {}).get("data", [])
    #     refund_id = refunds[0].get("id") if refunds else ""

    #     try:
    #         signup_record = SignUp.objects.get(payment_ref=payment_intent_id)         
    #         SignUpRefund.objects.create(
    #             sign_up=signup_record,
    #             refund_method="stripe",
    #             refund_amount=refund_amount,
    #             refund_ref=refund_id,
    #             created_by="System Webhook",
    #             last_updated_by="System Webhook",
    #         )
    #         print(f"退款紀錄已自動建立: 訂單 #{signup_record.id}")
            
    #     except SignUp.DoesNotExist:
    #         print(f"找不到對應的報名紀錄: {payment_intent_id}")

    return HttpResponse(status=200)

@frontweb_app_func.load_main_category
def payment_fail(request):
    course_id = request.GET.get('course_id')
    context = {'list_mc' : request.list_mc, "course_id" : course_id}
    return render(request, "payment_fail.html", context)
# endregion

# region View: Dashboard
@frontweb_app_func.load_main_category
@frontweb_app_func.student_access_control()
def student_dashboard(request):
    list_mode = "CurrentCourse" if (request.GET.get("ListMode") != "PastCourse" and request.GET.get("ListMode") != "PaymentHistory") else "PastCourse" if request.GET.get("ListMode") == "PastCourse" else "PaymentHistory"
    print(list_mode)
    context = {'list_mc' : request.list_mc, "list_mode" : list_mode}

    if list_mode == "CurrentCourse":
        context["list_course"] = Course.objects.annotate(course_end_datetime=ExpressionWrapper(F('period_to') + F('time_to'), output_field=DateTimeField())
        ).filter(signup_set__student_id=request.session.get('student_id'), 
                signup_set__sign_up_status='success',
                signup_set__cancel_date__isnull=True,
                course_end_datetime__gte=timezone.localtime(timezone.now()),
                course_status='created')
        
    elif list_mode == "PastCourse":
        context["list_course"] = Course.objects.annotate(course_end_datetime=ExpressionWrapper(F('period_to') + F('time_to'), output_field=DateTimeField())
        ).filter(signup_set__student_id=request.session.get('student_id'), 
                signup_set__sign_up_status='success',
                signup_set__cancel_date__isnull=True,
                course_end_datetime__lte=timezone.localtime(timezone.now()),
                course_status='created')
        
    elif list_mode == "PaymentHistory":
        #Get Payment
        payment_list = SignUp.objects.filter(student_id=request.session.get('student_id'), payment_date__isnull=False).exclude(file_status="deleted").annotate(
            record_type=Value('payment', output_field=CharField()),
            record_id=F('id'),
            display_course_name=F('course__name'),
            display_date=F('payment_date'),
            display_amount=F('payment_amount'),
            display_method=F('payment_method'),
            display_ref=F('payment_ref'),
            display_status=F('sign_up_status')
            ).values(
            'record_type', 
            'record_id',
            'display_course_name', 
            'display_date', 
            'display_amount', 
            'display_method', 
            'display_ref', 
            'display_status')

        #Get Refunds
        refund_list = SignUpRefund.objects.filter(sign_up__student_id=request.session.get('student_id'), refund_date__isnull=False).exclude(file_status="deleted").annotate(
            record_type=Value('refund', output_field=CharField()),
            record_id=F('id'),
            display_course_name=F('sign_up__course__name'),
            display_date=F('refund_date'),
            display_amount=F('refund_amount'),
            display_method=F('refund_method'),
            display_ref=F('refund_ref'),
            display_status=Value('refunded', output_field=CharField())
            ).values(
            'record_type', 
            'record_id',
            'display_course_name', 
            'display_date', 
            'display_amount', 
            'display_method', 
            'display_ref', 
            'display_status')

        #Union and sort by display date desc
        context["list_trans"] = payment_list.union(refund_list)

    return render(request, "student_dashboard.html", context)

@frontweb_app_func.student_access_control()
def download_payment_receipt(request, signup_id):
    obj_signup = get_object_or_404(SignUp, id=signup_id)
    
    pdf_bytes = courses_app_func.generate_payment_receipt_pdf(obj_signup)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Receipt_{obj_signup.payment_ref}.pdf"'
    
    return response

@frontweb_app_func.student_access_control()
def download_refund_receipt(request, refund_id):
    obj_refund = get_object_or_404(SignUpRefund, id=refund_id)
    
    pdf_bytes = courses_app_func.generate_refund_receipt_pdf(obj_refund)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Receipt_{obj_refund.refund_ref}.pdf"'
    
    return response
# endregion

