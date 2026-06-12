from administration.func import app_func as admin_app_func
from .models import Course, CourseMainCategory, CourseSubCategory, CourseTemplate, SignUp
from teachers.models import Teacher
from django.db.models import Q, F
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from urllib.parse import urlencode
from django.contrib import messages
from .func import app_func as course_app_func
from django.utils.dateparse import parse_date, parse_time
from django.utils import timezone
import json
from core.utils import decode_id
from django.http import Http404

# region Course
@admin_app_func.staff_access_control
def course_list(request):
    
    #Load Category for filter
    list_maincategory = CourseMainCategory.objects.filter(is_active=True)
    list_subcategory = CourseSubCategory.objects.filter(is_active=True)

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
            context = {"list_maincategory" : list_maincategory, "list_subcategory" : list_subcategory, "list_course" : list_course, "input_data" : request.POST}
            return render(request, "courses/course_list.html", context)
        
        #Get User filter and pass by redirect
        query_kwargs = {}
        if keyword:= request.POST.get('txtkeyword', '').strip():
            query_kwargs['txtkeyword'] = keyword

        if dynamic_status:= request.POST.get('StatusSelector', '').strip():
            query_kwargs['StatusSelector'] = dynamic_status

        if maincourse_category:= request.POST.get('MainCategorySelector', '').strip():
            query_kwargs['MainCategorySelector'] = maincourse_category

        if subcourse_category:= request.POST.get('SubCategorySelector', '').strip():
            query_kwargs['SubCategorySelector'] = subcourse_category

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

        if maincourse_category:= request.GET.get('MainCategorySelector', '').strip():
            course_filters['sub_category__main_category_id'] = maincourse_category

        if subcourse_category:= request.GET.get('SubCategorySelector', '').strip():
            course_filters['sub_category_id'] = subcourse_category

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

        #取得排序參數並套用 ORM 的 order_by
        sort_by = request.GET.get('sort_by', '').strip()
        sort_dir = request.GET.get('sort_dir', 'asc').strip() # 預設遞增 (asc)

        if sort_by:
            # 確保欄位名稱是合法的，防止惡意字串導致 ORM 報錯
            valid_sort_fields = ['code', 'name', 'is_web_publish', 'is_promote', 'registation_expiry_date', 'period_from', 'period_to', 'sub_category__name']
            if sort_by in valid_sort_fields:
                # 如果是 desc 就加上負號 '-' 來做遞減排序
                order_prefix = '-' if sort_dir == 'desc' else ''
                list_course = list_course.order_by(f"{order_prefix}{sort_by}")
        #End Sort
            
        context = {"list_maincategory" : list_maincategory, "list_subcategory" : list_subcategory, "list_course" : list_course, "input_data" : request.GET}
        return render(request, "courses/course_list.html", context)

@admin_app_func.staff_access_control
def course_create(request):

    list_templates = CourseTemplate.objects.exclude(file_status="deleted")
    list_subcategory = CourseSubCategory.objects.filter(is_active=True).exclude(file_status="deleted")
    list_teacher = Teacher.objects.filter(is_active=True).exclude(file_status="deleted")

    if request.method == "POST":

        #Check input Valid
        blnIsValid = True
        if not (name:= request.POST.get("name", '').strip()):
            messages.error(request, "課程名稱為必填欄位")
            blnIsValid = False

        if not (code:= request.POST.get("code", '').strip()):
            messages.error(request, "課程代碼為必填欄位")
            blnIsValid = False

        if not (sub_category_id:= request.POST.get("sub_category_id", '').strip()):
            messages.error(request, "請選擇課程類別")
            blnIsValid = False

        if not (course_fee:= request.POST.get("course_fee", '').strip()):
            messages.error(request, "請填寫課程費用")
            blnIsValid = False
        else:
            try:
                float(course_fee)
                if float(course_fee) <= 0:
                    messages.error(request, "課程費用必須大於 0")
                    blnIsValid = False
            except ValueError:
                messages.error(request, "課程費用格式錯誤，必須是數字")
                blnIsValid = False

        if not (total_lessons:=request.POST.get("total_lessons", '').strip()) or not total_lessons.isdigit() or int(total_lessons) <= 0:
            messages.error(request, "總堂數必須是大於 0 的整數")
            blnIsValid = False

        if not (max_no_student:=request.POST.get("max_no_student", '').strip()) or not max_no_student.isdigit() or int(max_no_student) <= 0:
            messages.error(request, "人數上限必須是大於 0 的整數")
            blnIsValid = False

        #Date Checking
        if not (registation_expiry_date:=parse_date(request.POST.get("registation_expiry_date", '').strip())) or not (period_from:=parse_date(request.POST.get("period_from", '').strip())) or not (period_to:=parse_date(request.POST.get("period_to", '').strip())):
            messages.error(request, "請輸入有效的日期格式")
            blnIsValid = False
        else:
            if registation_expiry_date <= timezone.now().date():
                messages.error(request, "報名截止日期必須 > 今天")
                blnIsValid = False
            if registation_expiry_date >= period_from:
                messages.error(request, "報名截止日期必須 < 開始日期")
                blnIsValid = False
            if  period_from > period_to:
                messages.error(request, "課程結束日期必須 >= 課程開始日期")
                blnIsValid = False

        #Time chacking
        if not (time_from:= parse_time(request.POST.get("time_from", '').strip())) or not (time_to:= parse_time(request.POST.get("time_to", '').strip())):
            messages.error(request, "請填寫有效的上課時間")
            blnIsValid = False
        else:
            if time_from >= time_to:
                messages.error(request, "上課結束時間必須 > 上課開始時間")
                blnIsValid = False
        
        if not blnIsValid:
            #Create dict from pass non-string value back to template
            temp_obj = request.POST.dict()
            temp_obj['period_from'] = period_from
            temp_obj['period_to'] = period_to
            temp_obj['registation_expiry_date'] = registation_expiry_date
            temp_obj['time_from'] = time_from
            temp_obj['time_to'] = time_to
            
            temp_obj['is_web_publish'] = request.POST.get("is_web_publish") == "on"
            temp_obj['is_promote'] = request.POST.get("is_promote") == "on"

            temp_obj['sub_category_id'] = int(sub_category_id) if sub_category_id  else None
            temp_obj['teacher_id'] = int(request.POST.get("teacher_id")) if request.POST.get("teacher_id") and request.POST.get("teacher_id").isdigit() else None

            context = {
                "form_mode" : "create",
                "list_templates": list_templates,
                "list_subcategory": list_subcategory,
                "list_teacher": list_teacher,
                "obj_course" : temp_obj,}
            return render(request, "courses/course_edit.html", context)

        #ORM Create
        Course.objects.create(
            sub_category_id=sub_category_id,
            teacher_id=request.POST.get("teacher_id") or None,
            center_id=request.POST.get("center") or None,
            
            code=code,
            name=name,
            content=request.POST.get("content", '').strip(),
            photo=request.FILES.get("photo"),
            
            feature_1=request.POST.get("feature_1", '').strip(),
            feature_2=request.POST.get("feature_2", '').strip(),
            feature_3=request.POST.get("feature_3", '').strip(),
            feature_4=request.POST.get("feature_4", '').strip(),
            feature_5=request.POST.get("feature_5", '').strip(),
            feature_6=request.POST.get("feature_6", '').strip(),
            feature_7=request.POST.get("feature_7", '').strip(),
            feature_8=request.POST.get("feature_8", '').strip(),
            
            course_fee=course_fee,
            total_lessons=total_lessons,
            hours_per_lesson=request.POST.get("hours_per_lesson") or 0,
            max_no_student=max_no_student,
            
            period_from=period_from,
            period_to=period_to,
            time_from=time_from,
            time_to=time_to,
            
            registation_expiry_date=registation_expiry_date,
            #default_room=request.POST.get("room", '').strip(),
            is_web_publish=request.POST.get("is_web_publish") == "on",
            is_promote=request.POST.get("is_promote") == "on",
            course_status="created" # 預設狀態
        )
        #Success
        messages.success(request, "課程建立成功！")
        return redirect("courses:course_list")
    else:
        context = {
            "form_mode" : "create",
            "list_templates": list_templates,
            "list_subcategory": list_subcategory,
            "list_teacher": list_teacher,}
        print(list_subcategory.count)
        return render(request, "courses/course_edit.html", context)

@admin_app_func.staff_access_control
def course_edit(request, course_hash):

    #decode hash id
    course_id = decode_id(course_hash)
    if not course_id:
        raise Http404("無效的課程連結")
    
    #Get course object & drop down list datasource
    obj_course = get_object_or_404(Course, Q(id=course_id) & ~Q(file_status="deleted"))
    list_templates = CourseTemplate.objects.exclude(file_status="deleted")
    list_subcategory = CourseSubCategory.objects.filter(is_active=True).exclude(file_status="deleted")
    list_teacher = Teacher.objects.filter(is_active=True).exclude(file_status="deleted")

    if request.method == "POST":

        #Check input Valid
        blnIsValid = True
        if not (name:= request.POST.get("name", '').strip()):
            messages.error(request, "課程名稱為必填欄位")
            blnIsValid = False

        if not (code:= request.POST.get("code", '').strip()):
            messages.error(request, "課程代碼為必填欄位")
            blnIsValid = False

        if not (sub_category_id:= request.POST.get("sub_category_id", '').strip()):
            messages.error(request, "請選擇課程類別")
            blnIsValid = False

        if not (course_fee:= request.POST.get("course_fee", '').strip()):
            messages.error(request, "請填寫課程費用")
            blnIsValid = False
        else:
            try:
                float(course_fee)
                if float(course_fee) <= 0:
                    messages.error(request, "課程費用必須大於 0")
                    blnIsValid = False
            except ValueError:
                messages.error(request, "課程費用格式錯誤，必須是數字")
                blnIsValid = False

        if not (total_lessons:=request.POST.get("total_lessons", '').strip()) or not total_lessons.isdigit() or int(total_lessons) <= 0:
            messages.error(request, "總堂數必須是大於 0 的整數")
            blnIsValid = False

        if not (max_no_student:=request.POST.get("max_no_student", '').strip()) or not max_no_student.isdigit() or int(max_no_student) <= 0:
            messages.error(request, "人數上限必須是大於 0 的整數")
            blnIsValid = False

        #Date Checking
        if not (registation_expiry_date:=parse_date(request.POST.get("registation_expiry_date", '').strip())) or not (period_from:=parse_date(request.POST.get("period_from", '').strip())) or not (period_to:=parse_date(request.POST.get("period_to", '').strip())):
            messages.error(request, "請輸入有效的日期格式")
            blnIsValid = False
        else:
            if registation_expiry_date <= timezone.now().date():
                messages.error(request, "報名截止日期必須 > 今天")
                blnIsValid = False
            if registation_expiry_date >= period_from:
                messages.error(request, "報名截止日期必須 < 開始日期")
                blnIsValid = False
            if  period_from > period_to:
                messages.error(request, "課程結束日期必須 >= 課程開始日期")
                blnIsValid = False

        #Time chacking
        if not (time_from:= parse_time(request.POST.get("time_from", '').strip())) or not (time_to:= parse_time(request.POST.get("time_to", '').strip())):
            messages.error(request, "請填寫有效的上課時間")
            blnIsValid = False
        else:
            if time_from >= time_to:
                messages.error(request, "上課結束時間必須 > 上課開始時間")
                blnIsValid = False
        
        if not blnIsValid:
            #Create dict from pass non-string value back to template
            temp_obj = request.POST.dict()
            temp_obj['id'] = course_id
            temp_obj['period_from'] = period_from
            temp_obj['period_to'] = period_to
            temp_obj['registation_expiry_date'] = registation_expiry_date
            temp_obj['time_from'] = time_from
            temp_obj['time_to'] = time_to
            
            temp_obj['is_web_publish'] = request.POST.get("is_web_publish") == "on"
            temp_obj['is_promote'] = request.POST.get("is_promote") == "on"

            temp_obj['sub_category_id'] = int(sub_category_id) if sub_category_id  else None
            temp_obj['teacher_id'] = int(request.POST.get("teacher_id")) if request.POST.get("teacher_id") and request.POST.get("teacher_id").isdigit() else None

            context = {
                "form_mode" : "edit",
                "obj_course": temp_obj,
                "list_templates": list_templates,
                "list_subcategory": list_subcategory,
                "list_teacher": list_teacher,}
            return render(request, "courses/course_edit.html", context)
        
        obj_course.sub_category_id=sub_category_id
        obj_course.teacher_id=request.POST.get("teacher_id") or None
        obj_course.center_id=request.POST.get("center") or None

        obj_course.code=code
        obj_course.name=name
        obj_course.content=request.POST.get("content", '').strip()
        if "photo" in request.FILES:
            obj_course.photo = request.FILES.get("photo")

        obj_course.feature_1=request.POST.get("feature_1", '').strip()
        obj_course.feature_2=request.POST.get("feature_2", '').strip()
        obj_course.feature_3=request.POST.get("feature_3", '').strip()
        obj_course.feature_4=request.POST.get("feature_4", '').strip()
        obj_course.feature_5=request.POST.get("feature_5", '').strip()
        obj_course.feature_6=request.POST.get("feature_6", '').strip()
        obj_course.feature_7=request.POST.get("feature_7", '').strip()
        obj_course.feature_8=request.POST.get("feature_8", '').strip()

        obj_course.course_fee=course_fee
        obj_course.total_lessons=total_lessons
        obj_course.hours_per_lesson=request.POST.get("hours_per_lesson") or 0
        obj_course.max_no_student=max_no_student

        obj_course.period_from=period_from
        obj_course.period_to=period_to
        obj_course.time_from=time_from
        obj_course.time_to=time_to

        obj_course.registation_expiry_date=registation_expiry_date
        #obj_course.default_room=request.POST.get("room", '').strip()
        obj_course.is_web_publish=request.POST.get("is_web_publish") == "on"
        obj_course.is_promote=request.POST.get("is_promote") == "on"

        obj_course.save()

        messages.success(request, "課程更新成功！")
        return redirect("courses:course_list")
    
    else:#GET
        context = {
            "form_mode" : "edit",
            "obj_course": obj_course,
            "list_templates": list_templates,
            "list_subcategory": list_subcategory,
            "list_teacher": list_teacher,}
        return render(request, "courses/course_edit.html", context)

@admin_app_func.staff_access_control
def course_delete(request, course_hash):

    #decode hash id
    course_id = decode_id(course_hash)
    if not course_id:
        raise Http404("無效的課程連結")

    #Check if any student signup already, if yes, only allow cancel
    if SignUp.objects.filter(course_id=course_id).exclude(file_status="deleted"):
        messages.error(request, "SignUp found, cannot delete, please consider cancel it")
        return redirect("courses:course_edit", course_id)
    else:
        obj_course = get_object_or_404(Course, (Q(id=course_id) & ~Q(file_status="deleted")))
        obj_course.delete()
        messages.success(request, "Deleted")
        return redirect("courses:course_list")
# endregion

@admin_app_func.staff_access_control
def course_view(request, course_hash):

    #decode hash id
    course_id = decode_id(course_hash)
    if not course_id:
        raise Http404("無效的課程連結")

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