# from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Student, GatepassRequest

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'roll_no', 'email', 'parent_contact')
    search_fields = ('name', 'roll_no', 'email')

@admin.register(GatepassRequest)
class GatepassRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'destination', 'status', 'date_time', 'duration', 'created_at')
    list_filter = ('status', 'date_time')
    search_fields = ('student__name', 'destination', 'purpose')
