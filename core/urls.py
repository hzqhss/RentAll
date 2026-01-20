from django.urls import path
from core import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="feed"), 
    path("post/<slug:slug>/", views.post_detail, name="post-detail"), 
    
    #ajax urls for posts
    path("create_post/", views.create_post, name="create_post"), 
    path("like_post/", views.like_post, name="like_post"), 
    path("comment_post/", views.comment_on_post, name="comment_post"), 
    path("like_comment/", views.like_comment, name="like_comment"), 
    path("like_reply/", views.like_reply, name="like_reply"), 
    path("reply_comment/", views.reply_comment, name="reply-comment"), 
    path("delete_comment/", views.delete_comment, name="delete-comment"), 
    path("delete_reply/", views.delete_reply, name="delete-reply"), 
    path("add-friend/", views.add_friend, name="add-friend"),
    path("unfriend/", views.unfriend, name="unfriend"),
    path("save-post/", views.save_post, name="save_post"),
    path("delete-post/", views.delete_post, name="delete_post"),
    path("add-item/", views.add_item, name="add-item"),
    path("item/<slug:slug>/", views.item_detail, name="item-detail"),
    path("messages/", views.messages_view, name="messages"),
    # API for messaging
    path("api/get-messages/<int:user_id>/", views.get_messages_api, name="get_messages_api"),
    path("start_rental_chat/<str:rr_id>/", views.start_rental_chat, name="start_rental_chat"),
    path("api/send-message/", views.send_message_api, name="send_message_api"),
    path("edit-item/<str:pid>/", views.edit_item, name="edit-item"),
    path("delete-item/<str:pid>/", views.delete_item, name="delete-item"),
    path("submit-report/", views.submit_report, name="submit-report"),
    path("notifications/", views.notification_list, name="notifications"),
    path("submit-user-report/", views.submit_user_report, name="submit-user-report"),
    path("rental-progress/", views.rental_progress, name="rental-progress"),
    path("create-rental-request/", views.create_rental_request, name="create-rental-request"),
    path("manage-rental-request/", views.manage_rental_request, name="manage-rental-request"),
    path("my-rental/", views.my_rental, name="my-rental"),
    path("invoice/<str:rr_id>/", views.invoice_view, name="invoice"),
    path("confirm-payment/<str:rr_id>/", views.confirm_payment, name="confirm-payment"),
    path("submit-review/<str:rr_id>/", views.submit_review, name="submit-review"),
    path("search/", views.search, name="search"),
    path("my-listings/", views.my_listings, name="my-listings"),
    
]  