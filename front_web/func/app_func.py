from courses.models import CourseMainCategory
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

# region clear login session
def clear_login_session(request):
    keys_to_clear = ['student_id', 'student_name']
    for key in keys_to_clear:
        if key in request.session:
            del request.session[key]

# region Email verification
def send_verification_email(request, student):

    try:
        #負責生成 Token、組裝網址並發信
        print("check 1")
        uid = urlsafe_base64_encode(force_bytes(student.id))
        print("check 2")
        token = token_generator.make_token(student)
        print("check 3")
        activation_url = request.build_absolute_uri(
        reverse('front_web:student_verifiy_email', kwargs={'uidb64': uid, 'token': token})
        )
    
        subject = "請啟用您的學生帳號"
        email_body = f"""親愛的 {student.cn_name} 同學，您好：
請點擊下方連結以啟用您的帳號：
{activation_url}
中心管理團隊 敬上"""
        print("check 4")
        send_mail(subject=subject, message=email_body, from_email=None, recipient_list=[student.email])
        print("check 5")
    except Exception as e:
        # Code that runs if an error happens
        print(f"An error occurred: {e}")
    

def verify_activation_token(student, token):
    #只負責驗證 Token 是否合法與過期，回傳 True/False
    if student is None:
        return False
    return token_generator.check_token(student, token)
# endregion

# Region reset password
# endregion