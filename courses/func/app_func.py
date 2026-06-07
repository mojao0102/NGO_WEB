import os
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML
from administration.models import Center

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
