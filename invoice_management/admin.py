from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Company, UserProfile, Invoice


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'invoice_number', 'contact_person', 'phone', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'code', 'invoice_number', 'contact_person']
    readonly_fields = ['code', 'created_at', 'updated_at']


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'プロファイル'
    readonly_fields = ['user_code', 'created_at', 'updated_at']


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)


# 既存のUserAdminを一旦解除して、カスタムのものを登録
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'auto_number', 'invoice_number', 'company', 'total_amount', 'invoice_date', 
        'due_date', 'payment_status', 'registered_by', 'created_at'
    ]
    list_filter = ['payment_status', 'invoice_date', 'company', 'created_at']
    search_fields = ['invoice_number', 'auto_number', 'company__name', 'description']
    list_editable = ['payment_status']
    readonly_fields = ['auto_number', 'total_amount', 'created_at', 'updated_at']
    date_hierarchy = 'invoice_date'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['registered_by']
        return self.readonly_fields
    
    def save_model(self, request, obj, form, change):
        if not change:  # 新規作成時のみ
            obj.registered_by = request.user
        super().save_model(request, obj, form, change)
