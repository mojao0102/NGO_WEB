from django.shortcuts import render, redirect
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime
from django.contrib import messages
from .models import Staff
from .func import app_func as admin_app_func

from courses.models import SignUp
from students.models import Student

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


# @admin_app_func.staff_access_control
# def dashboard(request):
#     return render(request, 'staff_dashboard.html', {'active_page': 'dashboard'})

@admin_app_func.staff_access_control
def dashboard(request):
    # 取得年份、月份（預設抓現在）
    year = request.GET.get('year', timezone.now().year)
    month = request.GET.get('month', timezone.now().month)

    try:
        year = int(year)
        month = int(month)
    except:
        year = timezone.now().year
        month = timezone.now().month

    # 過濾規則：只計算【已付款、未取消】的有效訂單
    base_filter = Q(
        cancel_date__isnull=True,   # 排除已取消訂單
        payment_date__isnull=False, # 只統計已付款訂單
    )

    # ====================== 1. 當月統計 ======================
    monthly_signups = SignUp.objects.filter(
        base_filter,
        payment_date__year=year,
        payment_date__month=month
    )
    monthly_revenue = monthly_signups.aggregate(total=Sum('payment_amount'))['total'] or 0
    monthly_student_distinct = monthly_signups.values('student__id').distinct().count()
    monthly_signup_total = monthly_signups.count()

    # ====================== 2. 當年統計 ======================
    yearly_signups = SignUp.objects.filter(
        base_filter,
        payment_date__year=year,
    )
    yearly_revenue = yearly_signups.aggregate(total=Sum('payment_amount'))['total'] or 0
    yearly_student_distinct = yearly_signups.values('student__id').distinct().count()
    yearly_signup_total = yearly_signups.count()

    # ====================== 3. 當年 1-12 月 每月營收 (長條圖數據) ======================
    month_revenue_list = []
    month_labels = [
        "Jan","Feb","Mar","Apr","May","Jun",
        "Jul","Aug","Sep","Oct","Nov","Dec"
    ]
    for m in range(1, 13):
        month_data = yearly_signups.filter(payment_date__month=m).aggregate(
            total=Sum('payment_amount')
        )
        val = month_data['total'] or 0
        month_revenue_list.append(float(val))

    # ====================== 4. 當月報名 Top5 學生 ======================
    top_students = (
        monthly_signups
        .values(
            'student__student_no',
            'student__cn_name',
            'student__en_name',
            'student__dob'
        )
        .annotate(signup_count=Count('id'))
        .order_by('-signup_count')[:5]
    )

    # 下拉選單數據
    current_year = timezone.now().year
    years = [current_year - 1, current_year, current_year + 1]
    months = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]

    context = {
        'active_page': 'dashboard',
        'year': year,
        'month': month,
        'years': years,
        'months': months,

        # 當月數據
        'monthly_revenue': monthly_revenue,
        'monthly_student_distinct': monthly_student_distinct,
        'monthly_signup_total': monthly_signup_total,

        # 當年數據
        'yearly_revenue': yearly_revenue,
        'yearly_student_distinct': yearly_student_distinct,
        'yearly_signup_total': yearly_signup_total,

        # 圖表數據
        'chart_labels': month_labels,
        'chart_data': month_revenue_list,

        # Top5 學生
        'top_students': top_students,
    }

    return render(request, 'staff_dashboard.html', context)

