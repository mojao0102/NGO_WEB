from administration.func import app_func as admin_app_func
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Teacher

@admin_app_func.staff_access_control
def teacher_list(request):
    teachers = Teacher.objects.exclude(file_status='deleted').order_by('-id')
    return render(request, "staff_teacher.html", {'teachers': teachers})

@admin_app_func.staff_access_control
def teacher_create(request):
    if request.method == 'POST':
        try:
            Teacher.objects.create(
                username=request.POST.get('username', '').strip(),
                password=request.POST.get('password', ''),
                teacher_no=request.POST.get('teacher_no', '').strip(),
                first_name=request.POST.get('first_name', '').strip(),
                last_name=request.POST.get('last_name', '').strip(),
                title=request.POST.get('title', '').strip(),
                phone=request.POST.get('phone', '').strip(),
                email=request.POST.get('email', '').strip(),
                remarks=request.POST.get('remarks', '').strip(),
            )
            messages.success(request, 'Teacher created successfully.')
            return redirect('teachers:teacher_list')
        except Exception as e:
            messages.error(request, f'Error: {e}')
            return render(request, "staff_teacher_create.html", {'input_data': request.POST})
    return render(request, "staff_teacher_create.html")

@admin_app_func.staff_access_control
def teacher_edit(request, teacher_id):
    teacher = Teacher.objects.get(id=teacher_id)
    if request.method == 'POST':
        try:
            teacher.username = request.POST.get('username', '').strip()
            teacher.password = request.POST.get('password', '')
            teacher.teacher_no = request.POST.get('teacher_no', '').strip()
            teacher.first_name = request.POST.get('first_name', '').strip()
            teacher.last_name = request.POST.get('last_name', '').strip()
            teacher.title = request.POST.get('title', '').strip()
            teacher.phone = request.POST.get('phone', '').strip()
            teacher.email = request.POST.get('email', '').strip()
            teacher.remarks = request.POST.get('remarks', '').strip()
            teacher.save()
            messages.success(request, 'Teacher updated successfully.')
            return redirect('teachers:teacher_list')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, "staff_teacher_edit.html", {'teacher': teacher})

@admin_app_func.staff_access_control
def teacher_view(request, teacher_id):
    teacher = Teacher.objects.get(id=teacher_id)
    return render(request, "staff_teacher_view.html", {'teacher': teacher})
