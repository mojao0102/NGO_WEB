from django.utils import timezone
from django.db.models import F, Value, CharField, ExpressionWrapper, DateTimeField
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from courses.models import Course, SignUp, SignUpRefund
from ..func import app_func as frontweb_app_func
from courses.func import app_func as courses_app_func

from core.utils import decode_id, encode_id
from django.http import Http404

import stripe

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
        list_trans = payment_list.union(refund_list).order_by("-display_date")

        #hash id
        for trans in list_trans:
            trans['record_id'] = encode_id(trans['record_id']) 

        context["list_trans"] = list_trans

    return render(request, "student_dashboard.html", context)

@frontweb_app_func.student_access_control()
def download_payment_receipt(request, hash_signup):

    signup_id = decode_id(hash_signup)
    if not signup_id:
        raise Http404("無效的連結")

    obj_signup = get_object_or_404(SignUp, id=signup_id)
    
    pdf_bytes = courses_app_func.generate_payment_receipt_pdf(obj_signup)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Receipt_{obj_signup.payment_ref}.pdf"'
    
    return response

@frontweb_app_func.student_access_control()
def download_refund_receipt(request, hash_refund):

    refund_id = decode_id(hash_refund)
    if not refund_id:
        raise Http404("無效的連結")

    obj_refund = get_object_or_404(SignUpRefund, id=refund_id)
    
    pdf_bytes = courses_app_func.generate_refund_receipt_pdf(obj_refund)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Receipt_{obj_refund.refund_ref}.pdf"'
    
    return response
# endregion