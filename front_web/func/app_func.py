from courses.models import CourseMainCategory, CourseSubCategory, Course, SignUp
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

def check_student_login(view_func):# Decorator for checking if student logged-in
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        #request.IsStudentActive = False if not request.session['student_id'] else True if get_object_or_404(Student, id=request.session['student_id']).is_active else False 
        if not request.session['student_id']:
            messages.error(request, "請先登入")
            return redirect("front_web:student_login")
        else:
            return view_func(request, *args, **kwargs)
    return _wrapped_view

def check_student_active(view_func):# Decorator for checking student's is_active
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not get_object_or_404(Student, id=request.session['student_id']).is_active:
            messages.error(request, "帳號已被系統管理員停權，請聯絡中心。")
            return redirect("front_web:student_login")
        else:
            return view_func(request, *args, **kwargs)
    return _wrapped_view

def check_student_emailverified(view_func):# Decorator for checking student email is verified
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not get_object_or_404(Student, id=request.session['student_id']).is_email_verified:
            messages.error(request, "您的電子郵件尚未驗證，請先完成驗證。")
            return redirect("front_web:register_pending")
        else:
            return view_func(request, *args, **kwargs)
    return _wrapped_view
# endregion

# region Email verification
def send_verification_email(request, student):
    #負責生成 Token、組裝網址並發信
    uid = urlsafe_base64_encode(force_bytes(student.id))
    token = token_generator.make_token(student)
    
    activation_url = request.build_absolute_uri(
        reverse('front_web:activate_account', kwargs={'uidb64': uid, 'token': token})
    )
    
    subject = "請啟用您的中心學生帳號"
    email_body = f"""親愛的 {student.cn_name} 同學，您好：
請點擊下方連結以啟用您的帳號：
{activation_url}
中心管理團隊 敬上"""

    send_mail(subject=subject, message=email_body, from_email=None, recipient_list=[student.email])


def verify_activation_token(student, token):
    #只負責驗證 Token 是否合法與過期，回傳 True/False
    if student is None:
        return False
    return token_generator.check_token(student, token)
# endregion

# Region reset password
# endregion