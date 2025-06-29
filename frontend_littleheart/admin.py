from django.contrib import admin
from django.contrib.auth.models import User
from .models import UserProfile, Contact, Blog, Booking

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_id_display', 'username_display', 'email_display', 'phone', 'address')
    search_fields = ('user__username', 'user__email', 'phone')
    readonly_fields = ('user',)

    def user_id_display(self, obj):
        return obj.user.id
    user_id_display.short_description = 'User ID'

    def username_display(self, obj):
        return obj.user.username
    username_display.short_description = 'Username'

    def email_display(self, obj):
        return obj.user.email
    email_display.short_description = 'Email'


    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')  # Optimize query with select_related





@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    search_fields = ('name', 'email', 'subject')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)

admin.site.register(UserProfile, UserProfileAdmin)



@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
    prepopulated_fields = {'slug': ('title',)}
    # Restrict to staff/admins (optional)
    def has_add_permission(self, request):
        return request.user.is_staff
    def has_change_permission(self, request, obj=None):
        return request.user.is_staff
    def has_delete_permission(self, request, obj=None):
        return request.user.is_staff
    

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'contact_no', 'date_time', 'status', 'total_price')
    list_filter = ('status', 'date_time')
    search_fields = ('full_name', 'contact_no', 'email')