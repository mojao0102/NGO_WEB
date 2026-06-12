import os
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML
from administration.models import Center
from django.db.models import Count, Case, When, Value, CharField, F, Q
from django.utils import timezone
from django.contrib import messages
from ..models import Course

def generate_payment_receipt_pdf(obj_signup):

    obj_center = Center.objects.first()       
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo', 'jc.png')
    logo_url = f"file://{logo_path}" if os.path.exists(logo_path) else ""

    context = {'signup': obj_signup, 'student': obj_signup.student, 'center': obj_center, 'logo_url': logo_url,}
    
    #渲染 HTML 並透過 WeasyPrint 轉成 PDF Bytes
    html_string = render_to_string('report_template/payment_receipt.html', context)
    pdf_bytes = HTML(string=html_string).write_pdf()
    
    return pdf_bytes

def generate_refund_receipt_pdf(obj_refund):

    obj_center = Center.objects.first()
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo', 'jc.png')
    logo_url = f"file://{logo_path}" if os.path.exists(logo_path) else ""
    
    context = {'refund': obj_refund, 'student': obj_refund.sign_up.student, 'center' : obj_center, "logo_url" : logo_url}

    html_string = render_to_string('report_template/refund_receipt.html', context)
    pdf_bytes = HTML(string=html_string).write_pdf()
    
    return pdf_bytes


def get_courses_with_dynamic_status(**kwargs):
    current_time = timezone.now()
    keyword = kwargs.pop('keyword', None)

    list_course = Course.objects.exclude(file_status="deleted").order_by("-created_datetime")

    if keyword:
        keyword = keyword.strip()
        list_course = list_course.filter(Q(name__icontains=keyword) | Q(code__icontains=keyword))

    if kwargs:
        list_course = list_course.filter(**kwargs)

    valid_signup_condition = (
        Q(signup_set__payment_date__isnull=False) &
        Q(signup_set__sign_up_status="success") & 
        Q(signup_set__cancel_date__isnull=True) & 
        ~Q(signup_set__file_status="deleted"))
    
    list_course = list_course.annotate(current_signup_count=Count('signup_set', filter=valid_signup_condition), 
                                    course_dynamic_status=Case(
                                    When(course_status='cancel', then=Value('已取消')),
                                    When(period_to__lt=current_time.date(), then=Value('已完結')),
                                    When(period_from__lte=current_time.date(),period_to__gte=current_time.date(),then=Value('進行中')),
                                    When(registation_expiry_date__lt=current_time, then=Value('截止報名')),
                                    When(current_signup_count__gte=F('max_no_student'), then=Value('人數已滿')),
                                    default=Value('報名中'),output_field=CharField()))
    return list_course

def course_set_publish(request, list_course_id):
    try:
        for id in list_course_id:
            temp_course = Course.objects.filter(id=id).update(is_web_publish=True, last_updated_by=request.obj_staff.username)
        return True
    except Exception as e:
        print(f"Course set web publish fail: {e}")
        messages.error(request, "Fail to set web publish")
        return False
    
def course_undo_publish(request, list_course_id):
    try:
        for id in list_course_id:
            temp_course = Course.objects.filter(id=id).update(is_web_publish=False, last_updated_by=request.obj_staff.username)
        return True
    except Exception as e:
        print(f"Course undo web publish fail: {e}")
        messages.error(request, "Fail to undo web publish")
        return False 

def course_set_promote(request, list_course_id):
    try:
        for id in list_course_id:
            temp_course = Course.objects.filter(id=id).update(is_promote=True, last_updated_by=request.obj_staff.username)
        return True
    except Exception as e:
        print(f"Course set web promote fail: {e}")
        messages.error(request, "Fail to set web promote")
        return False
    
def course_undo_promote(request, list_course_id):
    try:
        for id in list_course_id:
            temp_course = Course.objects.filter(id=id).update(is_promote=False, last_updated_by=request.obj_staff.username)
        return True
    except Exception as e:
        print(f"Course undo web promote fail: {e}")
        messages.error(request, "Fail to undo web promote")
        return False 
    
# --- 新增的共用表單驗證與解析函數 ---
def _validate_and_parse_course_form(request):

    #Return Tuple: (is_valid: bool, parsed_data: dict)

    is_valid = True
    # 預先拷貝 POST 資料，若驗證失敗可以直接傳回前端維持使用者輸入的內容
    parsed_data = request.POST.dict() 

    # 1. 必填文字欄位
    if not (name := request.POST.get("name", "").strip()):
        messages.error(request, "課程名稱為必填欄位")
        is_valid = False
    parsed_data["name"] = name
        
    if not (code := request.POST.get("code", "").strip()):
        messages.error(request, "課程代碼為必填欄位")
        is_valid = False
    parsed_data["code"] = code

    # 2. 關聯與數值欄位
    if not (sub_category_id := request.POST.get("sub_category_id", "").strip()):
        messages.error(request, "請選擇課程類別")
        is_valid = False
    parsed_data["sub_category_id"] = int(sub_category_id) if sub_category_id else None

    parsed_data["teacher_id"] = int(request.POST.get("teacher_id")) if request.POST.get("teacher_id") and request.POST.get("teacher_id").isdigit() else None
    
    parsed_data["center_id"] = request.POST.get("center") or None

    course_fee = request.POST.get("course_fee", "").strip()
    if not course_fee:
        messages.error(request, "請填寫課程費用")
        is_valid = False
    else:
        try:
            if float(course_fee) <= 0:
                messages.error(request, "課程費用必須大於 0")
                is_valid = False
        except ValueError:
            messages.error(request, "課程費用格式錯誤，必須是數字")
            is_valid = False

    total_lessons = request.POST.get("total_lessons", "").strip()
    if not total_lessons or not total_lessons.isdigit() or int(total_lessons) <= 0:
        messages.error(request, "總堂數必須是大於 0 的整數")
        is_valid = False

    max_no_student = request.POST.get("max_no_student", "").strip()
    if not max_no_student or not max_no_student.isdigit() or int(max_no_student) <= 0:
        messages.error(request, "人數上限必須是大於 0 的整數")
        is_valid = False

    # 3. 日期與時間邏輯 (含時區感知)
    registation_expiry_date = parse_datetime(request.POST.get("registation_expiry_date", "").strip())
    period_from = parse_date(request.POST.get("period_from", "").strip())
    period_to = parse_date(request.POST.get("period_to", "").strip())

    if not registation_expiry_date or not period_from or not period_to:
        messages.error(request, "請輸入有效的日期與時間格式")
        is_valid = False
    else:
        if timezone.is_naive(registation_expiry_date):
            registation_expiry_date = timezone.make_aware(registation_expiry_date)

        if registation_expiry_date <= timezone.now():
            messages.error(request, "報名截止時間必須晚於現在時間")
            is_valid = False
        if registation_expiry_date.date() > period_from:
            messages.error(request, "報名截止日期不能晚於課程開始日期")
            is_valid = False
        if period_from > period_to:
            messages.error(request, "課程結束日期必須 >= 課程開始日期")
            is_valid = False

        parsed_data["registation_expiry_date"] = registation_expiry_date
        parsed_data["period_from"] = period_from
        parsed_data["period_to"] = period_to

    time_from = parse_time(request.POST.get("time_from", "").strip())
    time_to = parse_time(request.POST.get("time_to", "").strip())

    if not time_from or not time_to:
        messages.error(request, "請填寫有效的上課時間")
        is_valid = False
    else:
        if time_from >= time_to:
            messages.error(request, "上課結束時間必須 > 上課開始時間")
            is_valid = False
        parsed_data["time_from"] = time_from
        parsed_data["time_to"] = time_to

    # 4. 其他雜項與開關
    parsed_data["is_web_publish"] = request.POST.get("is_web_publish") == "on"
    parsed_data["is_promote"] = request.POST.get("is_promote") == "on"
    parsed_data["hours_per_lesson"] = request.POST.get("hours_per_lesson") or 0
    parsed_data["content"] = request.POST.get("content", "").strip()
    
    # 陣列處理 (將星期陣列轉為字串)
    parsed_data["lesson_weekday_pattern"] = ",".join(request.POST.getlist("lesson_weekdays"))
    
    # 特徵欄位迴圈處理
    for i in range(1, 9):
        parsed_data[f"feature_{i}"] = request.POST.get(f"feature_{i}", "").strip()

    return is_valid, parsed_data