from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

staff_login_required = login_required(login_url='/administration/login/')


def staff_login(request):
    if request.user.is_authenticated:
        return redirect('administration:dashboard')
    if request.method == 'POST':
        user = authenticate(request,
                            username=request.POST.get('username', '').strip(),
                            password=request.POST.get('password', ''))
        if user and user.is_staff:
            login(request, user)
            return redirect('administration:dashboard')
        messages.error(request, '帳號或密碼錯誤，或沒有 Staff 權限')
        return render(request, 'administration/staff_login.html', {'input_data': request.POST})
    return render(request, 'administration/staff_login.html')


def staff_logout(request):
    logout(request)
    return redirect('administration:staff_login')


@staff_login_required
def dashboard(request):
    return render(request, 'administration/staff_dashboard.html', {'active_page': 'dashboard'})


@staff_login_required
def course_template(request):
    return render(request, 'administration/staff_course_template.html', {'active_page': 'course_template'})


@staff_login_required
def course_template_create(request):
    return render(request, 'administration/staff_course_template.html', {'active_page': 'course_template'})


@staff_login_required
def course(request):
    return render(request, 'administration/staff_course.html', {'active_page': 'course'})


@staff_login_required
def course_list(request):
    return render(request, 'administration/course_list.html', {'active_page': 'course'})


@staff_login_required
def course_create(request):
    return render(request, 'administration/course_create.html', {'active_page': 'course'})


@staff_login_required
def news(request):
    return render(request, 'administration/staff_news.html', {'active_page': 'news'})


@staff_login_required
def news_create(request):
    return render(request, 'administration/staff_news.html', {'active_page': 'news'})


@staff_login_required
def news_edit(request, pk):
    return render(request, 'administration/staff_news.html', {'active_page': 'news'})


@staff_login_required
def student(request):
    return render(request, 'administration/staff_student.html', {'active_page': 'student'})


@staff_login_required
def student_create(request):
    return render(request, 'administration/staff_student.html', {'active_page': 'student'})


@staff_login_required
def teacher(request):
    return render(request, 'administration/staff_teacher.html', {'active_page': 'teacher'})


@staff_login_required
def teacher_create(request):
    return render(request, 'administration/staff_teacher.html', {'active_page': 'teacher'})
