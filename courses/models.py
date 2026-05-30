from django.db import models
from colorfield.fields import ColorField

class CourseMainCategory(models.Model):

    name = models.CharField(max_length=50, null=True, verbose_name="主類別名稱")
    short_name = models.CharField(max_length=50, null=True, verbose_name="簡稱")
    desc = models.TextField(blank=True, null=True, verbose_name="描述")
    icon_class = models.CharField(max_length=100, verbose_name="Icon(FontAwesome Icon Class)", help_text="例如: fa-baby", blank=True, null=True)
    theme_color = ColorField(default="#FFFFFF", blank=True, null=True)
    file_status = models.CharField(max_length=100, blank=True, null=True, verbose_name="檔案狀態")
    created_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="建立者")
    created_datetime = models.DateTimeField(blank=True, null=True, verbose_name="建立時間", auto_now_add=True)
    last_updated_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="最後更新者")
    last_updated_datetime = models.DateTimeField(blank=True, null=True, verbose_name="最後更新時間", auto_now=True)

    class Meta:
        db_table = 'course_main_category'
        verbose_name = '課程主類別'
        verbose_name_plural = '課程主類別'

    def __str__(self):
        return self.name or f"MainCategory {self.id}"


class CourseSubCategory(models.Model):
    main_category = models.ForeignKey(CourseMainCategory, on_delete=models.CASCADE, db_column='main_category_id', verbose_name="所屬主類別")
    name = models.CharField(max_length=50, null=True, verbose_name="子類別名稱")
    short_name = models.CharField(max_length=50, null=True, verbose_name="簡稱")
    desc = models.TextField(blank=True, null=True, verbose_name="描述")
    file_status = models.CharField(max_length=100, blank=True, null=True, verbose_name="檔案狀態")
    created_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="建立者")
    created_datetime = models.DateTimeField(blank=True, null=True, verbose_name="建立時間", auto_now_add=True)
    last_updated_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="最後更新者")
    last_updated_datetime = models.DateTimeField(blank=True, null=True, verbose_name="最後更新時間", auto_now=True)

    class Meta:
        db_table = 'course_sub_category'
        verbose_name = '課程子類別'
        verbose_name_plural = '課程子類別'

    def __str__(self):
        return self.name or f"SubCategory {self.id}"
