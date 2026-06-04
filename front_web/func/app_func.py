from courses.models import CourseMainCategory
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from functools import wraps
from students.models import Student
from django.core.mail import send_mail
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse

# 初始化 Django 內建的安全 Token 產生器 (會自動處理過期與防重複點擊)
token_generator = PasswordResetTokenGenerator()

# region Decorator
def load_main_category(view_func):# Decorator for load main category for nav bar
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        request.list_mc = CourseMainCategory.objects.filter(is_active=True)      
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def student_access_control(require_email_verification=True):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            #Check if login
            if not request.session.get('student_id'):
                messages.error(request, "請先登入帳號")
                return redirect("front_web:student_login")

            try:#Check if student_exist
                obj_student = Student.objects.get(id=request.session.get('student_id'))
            except Student.DoesNotExist:
                messages.error(request, "帳號不存在，請聯絡中心")
                return redirect("front_web:student_login")
            
            #Check if student active
            if not obj_student.is_active:
                clear_login_session(request)
                messages.error(request, "帳號已被停權，請聯絡中心")
                return redirect("front_web:student_login")
            
            #Check if email verified
            if require_email_verification and not obj_student.is_email_verified:
                messages.warning(request, "您的電子郵件尚未驗證，請先完成驗證。")
                return redirect("front_web:student_register_pending")
            
            #For view's function to use
            request.obj_student = obj_student
            return view_func(request, *args, **kwargs)    
        return _wrapped_view
    return decorator
# endregion

# region create login session and update last login
def create_login_session(request, obj_student):
    request.session['student_id'] = obj_student.id
    request.session['student_name'] = obj_student.cn_name
    obj_student.last_login = timezone.localtime(timezone.now())
    obj_student.save()

# region clear login session
def clear_login_session(request):
    del request.session['student_id']
    del request.session['student_name']

# region Email verification
def verify_activation_token(student, token):
    #只負責驗證 Token 是否合法與過期，回傳 True/False
    if student is None:
        return False
    return token_generator.check_token(student, token)

def send_verification_email(request, student):
    try:
        uid = urlsafe_base64_encode(force_bytes(student.id))
        token = token_generator.make_token(student)
        activation_url = request.build_absolute_uri(
        reverse('front_web:student_verifiy_email', kwargs={'uidb64': uid, 'token': token})
        )
    
        subject = "請啟用您的學生帳號"
        email_body = f"""親愛的 {student.cn_name} 同學，您好：
請點擊下方連結以啟用您的帳號：
{activation_url}
中心管理團隊 敬上"""
        send_mail(subject=subject, message=email_body, from_email=None, recipient_list=[student.email])
    except Exception as e:
        print(f"An error occurred: {e}")

def send_password_reset_email(request, student):
    try:    
        uid = urlsafe_base64_encode(force_bytes(student.id))
        token = token_generator.make_token(student)
        reset_url = request.build_absolute_uri(
        reverse('front_web:student_reset_password', kwargs={'uidb64': uid, 'token': token})
        )
    
        subject = "【中心管理團隊】重設您的帳號密碼通知"
        email_body = f"""親愛的 {student.cn_name} 同學，您好：
系統收到您提出的重設密碼申請。請點擊或複製下方連結至瀏覽器以設定您的新密碼：
{reset_url}
(提示：此連結將於發信後 3 天內失效。如果您並未申請重設密碼，請直接忽略此郵件，您的密碼將保持不變。)
中心管理團隊 敬上"""
        send_mail(subject=subject, message=email_body, from_email=None, recipient_list=[student.email])
    except Exception as e:
        print(f"An error occurred: {e}")
# endregion
