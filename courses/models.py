from django.db import models
from colorfield.fields import ColorField
from .choices import course_status
from administration.models import Center, Room, Staff
from teachers.models import Teacher
from students.models import Student

class CourseMainCategory(models.Model):

    name = models.CharField(max_length=50, verbose_name="主類別名稱")
    short_name = models.CharField(max_length=50, verbose_name="簡稱")
    desc = models.TextField(blank=True, verbose_name="描述")
    nav_icon = models.CharField(max_length=100, verbose_name="Icon(FontAwesome Icon Class)", help_text="例如: fa-baby", blank=True, null=True)
    home_photo = models.ImageField(upload_to='main_category/%Y/%m/%d/', blank=True, null=True, verbose_name="首頁圖片")
    list_photo = models.ImageField(upload_to='sub_category/%Y/%m/%d/', blank=True, null=True, verbose_name="課程列表圖片")
    theme_color = ColorField(default="", blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name="是否啟用", help_text="是否可在用/顯示")
    file_status = models.CharField(max_length=100, blank=True, verbose_name="檔案狀態")
    created_by = models.CharField(max_length=100, blank=True, verbose_name="建立者")
    created_datetime = models.DateTimeField(blank=True, verbose_name="建立時間", auto_now_add=True)
    last_updated_by = models.CharField(max_length=100, blank=True, verbose_name="最後更新者")
    last_updated_datetime = models.DateTimeField(blank=True, verbose_name="最後更新時間", auto_now=True)

    class Meta:
        db_table = 'course_main_category'
        verbose_name = '課程主類別'
        verbose_name_plural = '課程主類別'

    def __str__(self):
        return self.name or f"MainCategory {self.id}"


class CourseSubCategory(models.Model):
    main_category = models.ForeignKey(CourseMainCategory, on_delete=models.CASCADE, db_column='main_category_id', verbose_name="所屬主類別")
    name = models.CharField(max_length=50, verbose_name="子類別名稱")
    short_name = models.CharField(max_length=50, verbose_name="簡稱")
    desc = models.TextField(blank=True, verbose_name="描述")
    list_photo = models.ImageField(upload_to='sub_category/%Y/%m/%d/', blank=True, verbose_name="課程列表圖片")
    is_active = models.BooleanField(default=True, verbose_name="是否啟用", help_text="是否可在用/顯示")
    file_status = models.CharField(max_length=100, blank=True, verbose_name="檔案狀態")
    created_by = models.CharField(max_length=100, blank=True, verbose_name="建立者")
    created_datetime = models.DateTimeField(blank=True, verbose_name="建立時間", auto_now_add=True)
    last_updated_by = models.CharField(max_length=100, blank=True, verbose_name="最後更新者")
    last_updated_datetime = models.DateTimeField(blank=True, verbose_name="最後更新時間", auto_now=True)

    class Meta:
        db_table = 'course_sub_category'
        verbose_name = '課程子類別'
        verbose_name_plural = '課程子類別'

    def __str__(self):
        return self.name or f"SubCategory {self.id}"
    
class CourseTemplate(models.Model):
    teacher = models.ForeignKey(Teacher, null=True, blank=True, on_delete=models.DO_NOTHING, related_name='templates', verbose_name="老師")
    sub_category = models.ForeignKey(CourseSubCategory, on_delete=models.DO_NOTHING, blank=True,  verbose_name="分類")   
    name = models.CharField(max_length=50, verbose_name="課程名稱")
    content = models.TextField(blank=True, verbose_name="課程介紹")
    
    # 彈性擴充特徵欄位
    feature_1 = models.CharField(max_length=200, blank=True, verbose_name="特徵 1")
    feature_2 = models.CharField(max_length=200, blank=True, verbose_name="特徵 2")
    feature_3 = models.CharField(max_length=200, blank=True, verbose_name="特徵 3")
    feature_4 = models.CharField(max_length=200, blank=True, verbose_name="特徵 4")
    feature_5 = models.CharField(max_length=200, blank=True, verbose_name="特徵 5")
    feature_6 = models.CharField(max_length=200, blank=True, verbose_name="特徵 6")
    feature_7 = models.CharField(max_length=200, blank=True, verbose_name="特徵 7")
    feature_8 = models.CharField(max_length=200, blank=True, verbose_name="特徵 8")
    
    total_lessons = models.DecimalField(max_digits=5, decimal_places=1, blank=True, verbose_name="總堂數")
    hours_per_lesson = models.DecimalField(max_digits=5, decimal_places=1, blank=True, verbose_name="每堂時數")
    total_hours = models.DecimalField(max_digits=5, decimal_places=1, blank=True, verbose_name="總時數")
    course_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, verbose_name="預設學費")
    is_active = models.BooleanField(default=True, verbose_name="是否啟用", help_text="控制此範本是否可在開課時被選用")
    
    # 內嵌 Audit Fields
    file_status = models.CharField(max_length=100, blank=True, verbose_name="狀態")
    created_by = models.CharField(max_length=100, blank=True, verbose_name="建立者")
    created_datetime = models.DateTimeField(auto_now_add=True, verbose_name="建立日期時間")
    last_updated_by = models.CharField(max_length=100, blank=True, verbose_name="最後更新者")
    last_updated_datetime = models.DateTimeField(auto_now=True, verbose_name="最後更新日期時間")

    class Meta:
        db_table = 'course_template'
        verbose_name = "課程範本"
        verbose_name_plural = "課程範本"
        ordering = ['-id']

    def __str__(self):
        return self.name

class Course(models.Model):
    template = models.ForeignKey(CourseTemplate, null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name="範本")
    sub_category = models.ForeignKey(CourseSubCategory, on_delete=models.DO_NOTHING, verbose_name="分類")
    teacher = models.ForeignKey(Teacher, on_delete=models.DO_NOTHING, verbose_name="老師")
    center = models.ForeignKey(Center, on_delete=models.DO_NOTHING,  null=True, blank=True, verbose_name="上課分校/中心")
    default_room = models.ForeignKey(Room, on_delete=models.DO_NOTHING, null=True, blank=True, verbose_name="預設上課教室")
    
    code = models.CharField(max_length=50, verbose_name="課程編號", help_text="例如：PY-2026-001")
    name = models.CharField(max_length=50, verbose_name="課程名稱")
    photo = models.ImageField(upload_to='course/%Y/%m/%d/', blank=True, verbose_name="首頁展示圖片")
    content = models.TextField(blank=True, verbose_name="課程介紹")
    
    feature_1 = models.CharField(max_length=200, blank=True, verbose_name="詳情 1")
    feature_2 = models.CharField(max_length=200, blank=True, verbose_name="詳情 2")
    feature_3 = models.CharField(max_length=200, blank=True, verbose_name="詳情 3")
    feature_4 = models.CharField(max_length=200, blank=True, verbose_name="詳情 4")
    feature_5 = models.CharField(max_length=200, blank=True, verbose_name="詳情 5")
    feature_6 = models.CharField(max_length=200, blank=True, verbose_name="詳情 6")
    feature_7 = models.CharField(max_length=200, blank=True, verbose_name="詳情 7")
    feature_8 = models.CharField(max_length=200, blank=True, verbose_name="詳情 8")
    
    age_group = models.CharField(max_length=200, blank=True, verbose_name="對象")

    total_lessons = models.DecimalField(max_digits=5, decimal_places=1, verbose_name="總上課堂數")
    hours_per_lesson = models.DecimalField(max_digits=5, decimal_places=1, blank=True, verbose_name="每堂上課時數")
    
    # 日期與時間 (v04 核心欄位：供前端扁平表單輸入)
    period_from = models.DateField(verbose_name="開始日期")
    period_to = models.DateField(verbose_name="結束日期")
    time_from = models.TimeField(blank=True, verbose_name="上課開始時間", help_text="格式如 14:00") 
    time_to = models.TimeField(blank=True, verbose_name="上課結束時間", help_text="格式如 16:00")
    lesson_weekday_pattern = models.CharField(max_length=200, blank=True, verbose_name="課程日期安排模式", help_text="格式如 逢星期六")

    course_fee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="學費") 
    max_no_student = models.IntegerField(verbose_name="人數上限")
    registation_expiry_date = models.DateTimeField(blank=True, verbose_name="截止時間")
    is_promote = models.BooleanField(default=False, verbose_name="是是否在首頁推薦?")
    is_web_publish = models.BooleanField(default=False, verbose_name="是否公開發布?")
    course_status = models.CharField(max_length=50, choices=course_status.items(), default="", verbose_name="課程狀態")

    # 內嵌 Audit Fields
    file_status = models.CharField(max_length=100, blank=True, verbose_name="狀態")
    created_by = models.CharField(max_length=100, blank=True, verbose_name="建立者")
    created_datetime = models.DateTimeField(auto_now_add=True, verbose_name="建立日期時間")
    last_updated_by = models.CharField(max_length=100, blank=True, verbose_name="最後更新者")
    last_updated_datetime = models.DateTimeField(auto_now=True, verbose_name="最後更新日期時間")

    class Meta:
        db_table = 'course'
        verbose_name = "課程"
        verbose_name_plural = "課程"
        ordering = ['-id']

    def __str__(self):
        return f"[{self.code}] {self.name}"


class CourseSchedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules', verbose_name="課程")
    day_of_week = models.IntegerField(verbose_name="毎星期", help_text="1=星期一, 2=星期二, ..., 7=星期日")
    start_time = models.TimeField(verbose_name="開始時間")
    end_time = models.TimeField(verbose_name="結束時間")

    file_status = models.CharField(max_length=100, blank=True, verbose_name="存檔狀態")
    created_by = models.CharField(max_length=100, blank=True, verbose_name="建立者")
    created_datetime = models.DateTimeField(auto_now_add=True, verbose_name="建立日期時間")
    last_updated_by = models.CharField(max_length=100, blank=True, verbose_name="最後更新者")
    last_updated_datetime = models.DateTimeField(auto_now=True, verbose_name="最後更新日期時間")

    class Meta:
        db_table = 'course_schedule'
        verbose_name = "課程排班表"
        verbose_name_plural = "課程排班表"
        ordering = ['course', 'day_of_week', 'start_time']

class SignUp(models.Model):
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING, related_name='signups', verbose_name="學生")
    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, related_name='signup_set', verbose_name="課程")
    status = models.CharField(max_length=50, blank=True, verbose_name="狀態")
    sign_up_date = models.CharField(max_length=50, blank=True, verbose_name="報名日期")
    
    # 審核/拒絕相關欄位
    is_reject = models.BooleanField(default=False, verbose_name="審核:拒絕報名")
    reject_date = models.DateTimeField(blank=True, verbose_name="拒絕時間")
    reject_by = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, null=True, blank=True, verbose_name="拒絕者")
    reject_reason = models.CharField(max_length=200, blank=True, verbose_name="拒絕原因")
    
    # 金流/付款相關欄位
    payment_date = models.DateTimeField(blank=True, verbose_name="付款時間")
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, verbose_name="付款金額")
    payment_method = models.CharField(max_length=50, blank=True, verbose_name="付款方式")
    payment_ref = models.CharField(max_length=50, blank=True, verbose_name="付款參考編號") # 👈 Stripe pi_*** 存這裡！
    payment_remarks = models.CharField(max_length=200, blank=True, verbose_name="付款備註")
    
    # 內嵌 Audit Fields (完全比照第一張圖的規格)
    file_status = models.CharField(max_length=100, blank=True, verbose_name="檔案狀態")
    created_by = models.CharField(max_length=100, blank=True, verbose_name="建立者")
    created_datetime = models.DateTimeField(auto_now_add=True, verbose_name="建立日期時間")
    last_updated_by = models.CharField(max_length=100, blank=True, verbose_name="最後更新者")
    last_updated_datetime = models.DateTimeField(auto_now=True, verbose_name="最後更新日期時間")

    class Meta:
        db_table = 'sign_up'
        verbose_name = "課程報名"
        verbose_name_plural = "課程報名"
        ordering = ['-id']

    def __str__(self):
        return f"{self.student} - {self.course}"