from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib import messages
from .models import Staff
from .func import app_func as admin_app_func

def staff_login(request):

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        try:
            obj_staff = Staff.objects.get(Q(username=username) & Q(password=password) & Q(is_active=True) & ~Q(file_status="deleted"))    
            admin_app_func.create_login_session(request, obj_staff)
            return redirect('administration:dashboard')
        
        except Staff.DoesNotExist:
            admin_app_func.clear_login_session(request)
            messages.error(request, '帳號或密碼錯誤，或沒有權限')
            return render(request, 'staff_login.html', {'input_data': request.POST})
        
        except Exception as e:
            print(f"staff login error, username:{username}, error:{e}")
            messages.error(request, '系統帳號異常，請聯絡中心管理員')
            return render(request, 'staff_login.html', {'input_data': request.POST})
    else:
        return render(request, 'staff_login.html')


@admin_app_func.staff_access_control
def staff_logout(request):
    if request.method == 'POST':
        admin_app_func.clear_login_session(request)
        messages.success(request, '登出成功')
        return redirect('administration:staff_login')
    else:    
        return redirect('administration:staff_dashboard')


@admin_app_func.staff_access_control
def dashboard(request):
    return render(request, 'staff_dashboard.html', {'active_page': 'dashboard'})


