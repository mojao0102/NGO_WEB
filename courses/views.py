from administration.func import app_func as admin_app_func
from .models import Course, CourseSubCategory
from django.db.models import Q, F
from django.shortcuts import render, redirect
from django.urls import reverse
from urllib.parse import urlencode
from django.contrib import messages
from .func import app_func as course_app_func

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
        keyword = request.POST.get('txtkeyword', '').strip()
        dynamic_status = request.POST.get('StatusSelector', '').strip()
        course_category = request.GET.get('CategorySelector', '').strip()

        query_kwargs = {}
        if keyword:
            query_kwargs['txtkeyword'] = keyword
        if dynamic_status:
            query_kwargs['StatusSelector'] = dynamic_status
        if course_category:
            query_kwargs['CategorySelector'] = course_category

        #reassemble the url with filter
        base_url = reverse('courses:course_list')
        if query_kwargs:
            redirect_url = f"{base_url}?{urlencode(query_kwargs)}"
        else:
            redirect_url = base_url

        #redirect with filter element
        return redirect(redirect_url)
    else:
        keyword = request.GET.get('txtkeyword', '').strip()
        dynamic_status = request.GET.get('StatusSelector', '').strip()
        course_category = request.GET.get('CategorySelector', '').strip()

        course_filters = {} 

        if keyword:
            course_filters['keyword'] = keyword
        if course_category:
            course_filters['sub_category_id'] = course_category

        list_course = course_app_func.get_courses_with_dynamic_status(**course_filters)

        #Filter annote field
        if dynamic_status:
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