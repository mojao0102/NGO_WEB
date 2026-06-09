from django.utils import timezone
from django.db.models import Q, F, Count, Case, When, Value, CharField
from django.shortcuts import render, get_object_or_404
from courses.models import CourseMainCategory, CourseSubCategory, Course
from web_contents.models import News
from ..func import app_func as frontweb_app_func, stripe_func

# region View: Course/Category
@frontweb_app_func.load_main_category
def course_list(request, mc_id):

    #Get main category object by id & is_active
    obj_mc = get_object_or_404(CourseMainCategory, id = mc_id, is_active = True)

    #Get sub category list by mc_id & is_active
    list_sc = CourseSubCategory.objects.filter(main_category_id = mc_id, is_active = True).order_by("-name")

    context = {'list_mc' : request.list_mc, 
                "obj_mc" : obj_mc, 
                "list_sc" : list_sc}

    #check if is from sc button press at web page or page/mc button load
    sc_id = int(request.GET['sc'] if 'sc' in request.GET else list_sc[0].id if list_sc else 0)

    #Get sub category object
    if sc_id > 0 :

        context["obj_sc"] = get_object_or_404(CourseSubCategory, id = sc_id, is_active = True)

        #Get course list
        course_queryset = Course.objects.annotate(
        valid_signup_count=Count('signup_set', filter=Q(signup_set__payment_date__isnull=False) 
                                & Q(signup_set__sign_up_status="success") 
                                & Q(signup_set__cancel_date__isnull=True)
                                & ~Q(signup_set__file_status="deleted"))
        ).annotate(
        #generate str_course_status base on valid_signup_count
            str_course_status=Case(
            When(
                max_no_student__gt=0, 
                valid_signup_count__gte=F('max_no_student'), 
                then=Value('名額已滿')
            ),
            default=Value('收生中'),
            output_field=CharField(),))
        
        #Only course with status "created", web published and not over registation expiry date allow to show
        context["list_course"] = course_queryset.filter(sub_category_id = sc_id, 
                                                is_web_publish = True, 
                                                registation_expiry_date__gt=timezone.localtime(timezone.now()),
                                                course_status = "created").exclude(file_status="deleted")
    return render(request, "course_list.html", context)

@frontweb_app_func.load_main_category
def course(request, course_id):
    
    if request.method == "POST":
        print("POST here")
    else:#GET
        #Get course object
        #Build custom field at course queryset
        #Count valid signup
        course_queryset = Course.objects.annotate(
        valid_signup_count=Count('signup_set', filter=Q(signup_set__payment_date__isnull=False) 
                                & Q(signup_set__sign_up_status="success") 
                                & Q(signup_set__cancel_date__isnull=True)
                                & ~Q(signup_set__file_status="deleted"))
        ).annotate(
        #generate str_course_status base on valid_signup_count
            str_course_status=Case(
            When(
                max_no_student__gt=0, 
                valid_signup_count__gte=F('max_no_student'), 
                then=Value('名額已滿')
            ),
            default=Value('收生中'),
            output_field=CharField(),))
        
        #Only course with status "created", web published and not over registation expiry date allow to show
        obj_course = get_object_or_404(course_queryset, id = course_id, 
                                    is_web_publish = True, 
                                    registation_expiry_date__gt=timezone.localtime(timezone.now()),
                                    course_status = "created").exclude(file_status="deleted")

        context = {'list_mc' : request.list_mc, "obj_course" : obj_course}

        return render(request, "course.html", context)
# endregion
