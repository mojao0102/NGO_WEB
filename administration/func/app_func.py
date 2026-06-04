from ..models import Staff
from django.utils import timezone
from django.contrib import messages
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404

#Decorator for check access
def staff_access_control(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        #Check if login
        if not request.session.get('staff_id'):
            messages.error(request, "請先登入帳號")
            return redirect("front_web:staff_login")
        try:#Check if staff
            obj_staff = Staff.objects.get(id=request.session.get('staff_id'))
        except Staff.DoesNotExist:
            messages.error(request, "帳號不存在，請聯絡系統管理員")
            return redirect("front_web:staff_login")
        
        #Check if staff active
        if not obj_staff.is_active:
            clear_login_session(request)
            messages.error(request, "帳號已被停權，請聯絡系統管理員")
            return redirect("front_web:staff_login")
        
        #For view's function to use
        request.obj_staff = obj_staff
        return view_func(request, *args, **kwargs)    
    return _wrapped_view

# region create login session and update last login
def create_login_session(request, obj_staff):
    request.session['staff_id'] = obj_staff.id
    request.session['staff_name'] = obj_staff.username
    obj_staff.last_login = timezone.localtime(timezone.now())
    obj_staff.save()

# region clear login session
def clear_login_session(request):
    #request.session.flush()
    request.session.pop('staff_id', None)
    request.session.pop('staff_name', None)
