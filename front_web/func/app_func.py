from courses.models import CourseMainCategory, CourseSubCategory, Course, SignUp
from functools import wraps

# region Decorator
def load_main_category(view_func):# Decorator for load main category for nav bar
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        request.list_mc = CourseMainCategory.objects.filter(is_active=True)      
        return view_func(request, *args, **kwargs)
    return _wrapped_view
# endregion