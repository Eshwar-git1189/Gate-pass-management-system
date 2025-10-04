from django.contrib import admin
from .models import Student, Parent, Gatepass, Approval, Profile

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'roll_no', 'get_email')
    search_fields = ('profile__user__first_name', 'profile__user__last_name', 'roll_no')

    @admin.display(description='Name')
    def get_full_name(self, obj):
        if obj.profile and obj.profile.user:
            return obj.profile.user.get_full_name() or obj.profile.user.username
        return "N/A"

    @admin.display(description='Email')
    def get_email(self, obj):
        if obj.profile and obj.profile.user:
            return obj.profile.user.email
        return "N/A"

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone')

@admin.register(Gatepass)
class GatepassAdmin(admin.ModelAdmin):
    list_display = ('student', 'destination', 'status', 'from_time', 'to_time', 'request_expires_at')
    list_filter = ('status',)

@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ('gatepass', 'parent', 'status', 'order', 'responded_at')
    list_filter = ('status',)
    search_fields = ('gatepass__student__name', 'parent__name')

admin.site.register(Profile)
