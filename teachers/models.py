from django.db import models

# Create your models here.
from django.db import models

class Teacher(models.Model):
    teacher_no = models.CharField(max_length=50, blank=True, verbose_name="導師編號")
    title = models.CharField(max_length=50, blank=True, verbose_name="稱謂/職稱")
    first_name = models.CharField(max_length=50, verbose_name="名字")
    last_name = models.CharField(max_length=50, verbose_name="姓氏")
    phone = models.CharField(max_length=50, verbose_name="電話")
    email = models.CharField(max_length=200, verbose_name="電子郵件")
    addr = models.CharField(max_length=200, blank=True, verbose_name="地址")
    dob = models.DateField(blank=True, verbose_name="出生日期")
    username = models.CharField(max_length=50, blank=True, verbose_name="帳號")
    password = models.CharField(max_length=50, blank=True, verbose_name="密碼")
    remarks = models.TextField(blank=True, verbose_name="備註")
    is_active = models.BooleanField(default=True, verbose_name="是否啟用")

    last_login = models.DateTimeField(null=True, blank=True)

    file_status = models.CharField(max_length=100, blank=True, verbose_name="檔案狀態")
    created_by = models.CharField(max_length=100, blank=True, verbose_name="建立者")
    created_datetime = models.DateTimeField(blank=True, verbose_name="建立時間", auto_now_add=True)
    last_updated_by = models.CharField(max_length=100, blank=True, verbose_name="最後更新者")
    last_updated_datetime = models.DateTimeField(blank=True, verbose_name="最後更新時間", auto_now=True)

    class Meta:
        db_table = 'teacher'
        verbose_name = '導師'
        verbose_name_plural = '導師'

    def __str__(self):
        return f"{self.teacher_no} - {self.first_name} {self.last_name}"
    
    def get_email_field_name(self):
        return "email"