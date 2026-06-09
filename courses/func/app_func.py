import os
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML
from administration.models import Center
from django.db.models import Count, Case, When, Value, CharField, F, Q
from django.utils import timezone
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


def get_courses_with_dynamic_status(keyword=None, **kwargs):
    today = timezone.now().date()

    list_course = Course.objects.exclude(file_status="deleted")

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
                                    When(period_to__lt=today, then=Value('已完結')),
                                    When(period_from__lte=today,period_to__gte=today,then=Value('進行中')),
                                    When(registation_expiry_date__lt=today, then=Value('截止報名')),
                                    When(current_signup_count__gte=F('max_no_student'), then=Value('人數已滿')),
                                    default=Value('報名中'),output_field=CharField()))
    return list_course
