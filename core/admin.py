from django.contrib import admin
#from core.models import Post, Gallery, Friend, FriendRequest, Comment, ReplyComment, Notification, Group, GroupPost, Page, PagePost, SavedPost
from core.models import (Post, Friend, Comment, ReplyComment, Notification, SavedPost, PostThumbnail, Product, DisputeReport, RentalRequest, Review)
from core.models import ChatMessage
from django.utils.safestring import mark_safe

# Register your models here.
#user boleh upload byk gambaq
class GalleryAdminTab(admin.TabularInline):
    model = PostThumbnail
    extra = 1 
    readonly_fields = ('image_tag',) 
    
    def image_tag(self, obj): 
        if obj.image: 
            return mark_safe(f'<img src="/media/{obj.image}" width="50" height="50" />') 
        return "-" 
    image_tag.short_description = 'Image'

class ReplyCommentTabAdmin(admin.TabularInline):
    model = ReplyComment

class PostAdmin(admin.ModelAdmin):
    inlines = [GalleryAdminTab]
    list_editable = ['active']
    list_display = ['thumbnail', 'user', 'title', 'visibility', 'active']
    prepopulated_fields = {"slug": ("title", )}
    filter_horizontal = ['likes', 'saved']

class SavedPostAdmin(admin.ModelAdmin):
    list_display = ['thumbnail', 'user', 'title', 'saved_by_count', 'visibility', 'active']
    search_fields = ['title', 'user__username']

    def get_queryset(self, request):
        # Filter to show only posts that have been saved by at least one user.
        return super().get_queryset(request).filter(saved__isnull=False).distinct()

    def saved_by_count(self, obj):
        return obj.saved.count()
    saved_by_count.short_description = 'Times Saved' # Sets the column header

# class GalleryAdmin(admin.ModelAdmin):
#     list_editable = ['active']
#     list_display = ['thumbnail', 'post', 'active']

class FriendAdmin(admin.ModelAdmin):
    list_display = ['user', 'friend', 'is_active']

class CommentAdmin(admin.ModelAdmin):
    inlines = [ReplyCommentTabAdmin]
    list_display = ['user', 'post', 'comment', 'active']

class ReplyAdmin(admin.ModelAdmin):
    list_display = ['user', 'comment', 'reply' , 'active']

class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'sender', 'post', 'comment', 'dispute', 'is_read', 'date']    

class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'message', 'is_read', 'date']

class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'daily_rate', 'date']

class RentalRequestAdmin(admin.ModelAdmin):
    list_display = ['product', 'renter', 'owner', 'status', 'start_date', 'end_date', 'date']
    list_filter = ['status', 'date']

class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'reviewer', 'rating', 'date']

class DisputeReportAdmin(admin.ModelAdmin):
    list_editable = ['status']
    list_display = ['reporter', 'product', 'reported_user', 'product_owner', 'reason', 'status', 'date']
    list_filter = ['status', 'reason']
    search_fields = ['reporter__username', 'product__title', 'reported_user__username', 'description']

    def product_owner(self, obj):
        if obj.product:
            return obj.product.user
        return None
    product_owner.short_description = 'Product Owner'
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            # Notify the reporter about the status change
            Notification.objects.create(
                user=obj.reporter,
                sender=request.user, # Admin user
                notification_type="Dispute Status Update",
                dispute=obj
            )
            # Notify the product owner or the reported user
            if obj.product:
                recipient = obj.product.user
            elif obj.reported_user:
                recipient = obj.reported_user
            else:
                recipient = None

            if recipient and recipient != obj.reporter:
                Notification.objects.create(
                    user=recipient,
                    sender=request.user, # Admin user
                    notification_type="Dispute Status Update",
                    dispute=obj
                )
        super().save_model(request, obj, form, change)


admin.site.register(SavedPost, SavedPostAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Friend, FriendAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(ReplyComment, ReplyAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(DisputeReport, DisputeReportAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)
admin.site.register(RentalRequest, RentalRequestAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Product, ProductAdmin)
