import json

from administration.func import app_func as admin_app_func
from django.shortcuts import render, redirect, get_object_or_404
from .models import CourseTemplate, CourseSubCategory, Course
from teachers.models import Teacher

def _template_context():
    return {
        'sub_categories': CourseSubCategory.objects.select_related('main_category').filter(is_active=True),
        'teachers': Teacher.objects.filter(is_active=True),
    }

@admin_app_func.staff_access_control
def course_template_list(request):
    qs = CourseTemplate.objects.select_related('teacher', 'sub_category__main_category').all()
    q = request.GET.get('q', '').strip()
    cat = request.GET.get('category', '').strip()
    if q:
        qs = qs.filter(name__icontains=q)
    if cat:
        qs = qs.filter(sub_category_id=cat)
    sub_categories = CourseSubCategory.objects.select_related('main_category').filter(is_active=True)
    return render(request, "courses/staff_coursetemplate.html", {
        'templates': qs,
        'sub_categories': sub_categories,
        'q': q,
        'selected_category': cat,
    })

@admin_app_func.staff_access_control
def course_template_create(request):
    if request.method == 'POST':
        p = request.POST
        CourseTemplate.objects.create(
            sub_category_id=p.get('sub_category') or None,
            teacher_id=p.get('teacher') or None,
            name=p.get('name', ''),
            content=p.get('content', ''),
            **{f'feature_{i}': p.get(f'feature_{i}', '') for i in range(1, 9)},
            total_lessons=p.get('total_lessons') or 0,
            hours_per_lesson=p.get('hours_per_lesson') or 0,
            total_hours=p.get('total_hours') or 0,
            course_fee=p.get('course_fee') or 0,
        )
        return redirect('courses:course_template_list')
    ctx = _template_context()
    ctx['features'] = [''] * 8
    return render(request, "courses/staff_coursetemplate_create&edit.html", ctx)

@admin_app_func.staff_access_control
def course_template_edit(request, template_id):
    tmpl = get_object_or_404(CourseTemplate, id=template_id)
    if request.method == 'POST':
        p = request.POST
        if p.get('action') == 'delete':
            tmpl.delete()
            return redirect('courses:course_template_list')
        tmpl.sub_category_id = p.get('sub_category') or None
        tmpl.teacher_id = p.get('teacher') or None
        tmpl.name = p.get('name', '')
        tmpl.content = p.get('content', '')
        for i in range(1, 9):
            setattr(tmpl, f'feature_{i}', p.get(f'feature_{i}', ''))
        tmpl.total_lessons = p.get('total_lessons') or 0
        tmpl.hours_per_lesson = p.get('hours_per_lesson') or 0
        tmpl.total_hours = p.get('total_hours') or 0
        tmpl.course_fee = p.get('course_fee') or 0
        tmpl.save()
        return redirect('courses:course_template_list')
    ctx = _template_context()
    ctx['template'] = tmpl
    ctx['features'] = [getattr(tmpl, f'feature_{i}', '') for i in range(1, 9)]
    return render(request, "courses/staff_coursetemplate_create&edit.html", ctx)

@admin_app_func.staff_access_control
def course_list(request):
    courses = Course.objects.select_related('sub_category', 'teacher').all()
    return render(request, "courses/course_list.html", {'courses': courses})

@admin_app_func.staff_access_control
def course_create(request):
    if request.method == 'POST':
        p = request.POST
        if not p.get('period_from') or not p.get('period_to') or not p.get('sub_category') or not p.get('teacher') or not p.get('registation_expiry_date'):
            return redirect(request.path)
        Course.objects.create(
            template_id=p.get('template') or None,
            sub_category_id=p.get('sub_category') or None,
            teacher_id=p.get('teacher') or None,
            code=p.get('code', ''),
            name=p.get('name', ''),
            content=p.get('content', ''),
            **{f'feature_{i}': p.get(f'feature_{i}', '') for i in range(1, 9)},
            course_fee=p.get('course_fee') or 0,
            total_lessons=p.get('total_lessons') or 0,
            hours_per_lesson=p.get('hours_per_lesson') or 0,
            period_from=p.get('period_from') or None,
            period_to=p.get('period_to') or None,
            time_from=p.get('time_from') or None,
            time_to=p.get('time_to') or None,
            registation_expiry_date=p.get('registation_expiry_date') or None,
            max_no_student=p.get('max_no_student') or 0,
            is_web_publish='is_web_publish' in p,
            is_promote='is_promote' in p,
            course_status=p.get('course_status', 'created'),
        )
        return redirect('courses:course_list')
    templates = CourseTemplate.objects.select_related('sub_category').filter(is_active=True)
    templates_data = {
        str(t.id): {
            'name': t.name,
            'content': t.content,
            'sub_category_id': t.sub_category_id,
            'teacher_id': t.teacher_id,
            'course_fee': str(t.course_fee),
            'total_lessons': str(t.total_lessons),
            'hours_per_lesson': str(t.hours_per_lesson),
            'total_hours': str(t.total_hours),
            'features': [getattr(t, f'feature_{i}', '') for i in range(1, 9)],
        }
        for t in templates
    }
    return render(request, "courses/course_edit.html", {
        'course_templates': templates,
        'templates_data_json': json.dumps(templates_data),
        'sub_categories': CourseSubCategory.objects.select_related('main_category').filter(is_active=True),
        'teachers': Teacher.objects.filter(is_active=True),
    })

@admin_app_func.staff_access_control
def course_edit(request, course_id):
    return render(request, "courses/course_edit.html")

@admin_app_func.staff_access_control
def course_view(request, course_id):
    return render(request, "courses/course_view.html")