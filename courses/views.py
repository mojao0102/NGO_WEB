from administration.func import app_func as admin_app_func
from .models import Course, CourseSubCategory, CourseTemplate
from teachers.models import Teacher
from django.db.models import Q, F
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from urllib.parse import urlencode
from django.contrib import messages
from .func import app_func as course_app_func
from django.utils.dateparse import parse_date
import json

# region Course
@admin_app_func.staff_access_control
def course_list(request):
    
    #Load Category for filter
    list_category = CourseSubCategory.objects.filter(is_active=True)

    if request.method == "POST" and request.POST.get("btnAction", '').strip() and request.POST.getlist("ceSelectedCourses"):

        list_id = request.POST.getlist("ceSelectedCourses")

        if request.POST.get("btnAction", '').strip() == "SetWebPublish":
            course_app_func.course_set_publish(request, list_id)
        elif request.POST.get("btnAction", '').strip() == "UndoWebPublish":
            course_app_func.course_undo_publish(request, list_id)
        elif request.POST.get("btnAction", '').strip() == "SetPromote":
            course_app_func.course_set_promote(request, list_id)
        elif request.POST.get("btnAction", '').strip() == "UndoPromote":    
            course_app_func.course_undo_promote(request, list_id)        
        else:
            messages.error(request, "unknown action")
            context = {"list_category" : list_category, "list_course" : list_course, "input_data" : request.POST}
            return render(request, "courses/course_list.html", context)
        
        #Get User filter and pass by redirect
        query_kwargs = {}
        if keyword:= request.POST.get('txtkeyword', '').strip():
            query_kwargs['txtkeyword'] = keyword

        if dynamic_status:= request.POST.get('StatusSelector', '').strip():
            query_kwargs['StatusSelector'] = dynamic_status

        if course_category:= request.POST.get('CategorySelector', '').strip():
            query_kwargs['CategorySelector'] = course_category

        if (publish_status := request.GET.get('PublishSelector', '').strip()) in ('0', '1'):
            query_kwargs['PublishSelector'] = publish_status

        if (promote_status := request.GET.get('PromoteSelector', '').strip()) in ('0', '1'):
            query_kwargs['PromoteSelector'] = promote_status

        if start_date_from:= parse_date(request.POST.get('start_date_from', '').strip()):
            query_kwargs['start_date_from'] = start_date_from

        if start_date_to:= parse_date(request.POST.get('start_date_to', '').strip()):
            query_kwargs['start_date_to'] = start_date_to

        if expiry_date_from:= parse_date(request.POST.get('expiry_date_from', '').strip()):
            query_kwargs['expiry_date_from'] = expiry_date_from

        if expiry_date_to:= parse_date(request.POST.get('expiry_date_to', '').strip()):
            query_kwargs['expiry_date_to'] = expiry_date_to

        #reassemble the url with filter
        base_url = reverse('courses:course_list')
        if query_kwargs:
            redirect_url = f"{base_url}?{urlencode(query_kwargs)}"
        else:
            redirect_url = base_url

        #redirect with filter element
        return redirect(redirect_url)
    else:#GET
        course_filters = {} 

        if keyword:= request.GET.get('txtkeyword', '').strip():
            course_filters['keyword'] = keyword

        if course_category:= request.GET.get('CategorySelector', '').strip():
            course_filters['sub_category_id'] = course_category

        if (publish_status := request.GET.get('PublishSelector', '').strip()) in ('0', '1'):
            course_filters['is_web_publish'] = (publish_status == '1')

        if (promote_status := request.GET.get('PromoteSelector', '').strip()) in ('0', '1'):
            course_filters['is_promote'] = (promote_status == '1')

        if start_date_from:= parse_date(request.GET.get('start_date_from', '').strip()):
            course_filters['period_from__gte'] = start_date_from

        if start_date_to:= parse_date(request.GET.get('start_date_to', '').strip()):
            course_filters['period_from__lte'] = start_date_to

        if expiry_date_from:= parse_date(request.GET.get('expiry_date_from', '').strip()):
            course_filters['registation_expiry_date__gte'] = expiry_date_from

        if expiry_date_to:= parse_date(request.GET.get('expiry_date_to', '').strip()):
            course_filters['registation_expiry_date__lte'] = expiry_date_to

        list_course = course_app_func.get_courses_with_dynamic_status(**course_filters)

        #Filter annote field
        if dynamic_status:= request.GET.get('StatusSelector', '').strip():
            list_course = list_course.filter(course_dynamic_status=dynamic_status)
            
        context = {"list_category" : list_category, "list_course" : list_course, "input_data" : request.GET}
        return render(request, "courses/course_list.html", context)

@admin_app_func.staff_access_control
def course_create(request):
    return render(request, "courses/course_edit.html")

@admin_app_func.staff_access_control
def course_edit(request, course_id):
    return render(request, "courses/course_edit.html")

@admin_app_func.staff_access_control
def course_view(request, course_id):
    return render(request, "courses/course_view.html")
# endregion

# region CourseTemplate
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
# endregion