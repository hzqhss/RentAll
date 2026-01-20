from django.db import models
from userauths.models import User, Profile, user_directory_path
from django.utils.text import slugify
from django.utils.html import mark_safe

from shortuuid.django_fields import ShortUUIDField
import shortuuid
import os

VISIBILITY = (
    ("General", "General"),
    ("Open for Rent", "Open for Rent"),
    ("Looking to Rent", "Looking to Rent")
)

AVAILABILITY = (
    ("available", "Available"),
    ("rented", "Rented"),
    ("unavailable", "Unavailable"),
)

RENTAL_STATUS = (
    ("Pending", "Pending"),
    ("Approved", "Approved"),
    ("Declined", "Declined"),
    ("Paid", "Paid"),
    ("Ongoing", "Ongoing"),
    ("Completed", "Completed"),
    ("Cancelled", "Cancelled"),
)

DISPUTE_STATUS = (
    ("pending", "Pending"),
    ("under_review", "Under Review"),
    ("resolved", "Resolved"),
    ("dismissed", "Dismissed"),
)

NOTIFICATION_TYPE = (
    ("New Like", "New Like"),
    ("New Follower", "New Follower"),
    ("New Comment", "New Comment"),
    ("Comment Liked", "Comment Liked"),
    ("Comment Replied", "Comment Replied"),
    ("Friend Added", "Friend Added"),
    ("Dispute Report", "Dispute Report"),
    ("Dispute Status Update", "Dispute Status Update"),
    ("Rental Request", "Rental Request"),
    ("Rental Request Approved", "Rental Request Approved"),
    ("Rental Request Declined", "Rental Request Declined"),
    ("Item Handed Over", "Item Handed Over"),
    ("Item Received", "Item Received"),
    ("Item Returned", "Item Returned"),
    ("Rental Request Cancelled", "Rental Request Cancelled"),
    ("Payment Completed", "Payment Completed"),
    ("Rental Period Ended", "Rental Period Ended"),
    ("Rental Completed", "Rental Completed"),
)

# Create your models here. model -> buat database
class Post(models.Model): #hold semua post yg user buat
    user = models.ForeignKey(User, on_delete=models.CASCADE) #delete user --> all the post got deleted too
    title = models.CharField(max_length=5000, blank=True, null=True) #title = caption,  tak dak caption pun boleh
    #video = models.FileField(upload_to=user_directory_path, blank=True, null=True)
    visibility = models.CharField(max_length=100, choices=VISIBILITY, default="General")
    pid = ShortUUIDField(length=7, max_length=25, alphabet='abcdefghijklmnopqrstuvwxyz')
    likes = models.ManyToManyField(User, blank=True, related_name="likes") #1 post: many likes
    active = models.BooleanField(default=True)
    slug = models.SlugField(max_length=255, unique=True) #each post =/ same slug
    view = models.PositiveIntegerField(default=0) #new post -> 0 view
    date = models.DateTimeField(auto_now_add=True) #grab time when user buat post automatically
    saved = models.ManyToManyField(User, related_name="saved", blank=True) #many users can save many posts
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True, related_name="rental_posts")

    def __str__(self):
        if self.title:
            return self.title
        else:
            return self.user.username
        
    #overwrite save method
    def save(self, *args, **kwargs):
        uuid_key = shortuuid.uuid() #give random key whenever kita call 
        uniqueid = uuid_key[:2]  # cut it to only the first 2
        if self.slug == "" or self.slug == None:
            self.slug = slugify(self.title) + '-' + uniqueid #lorem-ipsum-op (cth: unique string)

        #save model
        super(Post, self).save(*args, **kwargs)

    def thumbnail(self):
        thumb = self.post_thumbnail.first()  # Get the first PostThumbnail related to this Post
        if thumb and thumb.image:
            return mark_safe('<img src="/media/%s" width="50" height="50" object-fit:"cover" style="border-radius: 5px;" />' % (thumb.image))   
        return "-"
    
    def post_comment(self):
        comments = Comment.objects.filter(post=self, active=True).order_by("-date") #new comment on top
        return comments
    
class PostThumbnail(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="post_thumbnail"
    )
    class Meta:
        verbose_name_plural = 'Gallery'
    
    def gallery_upload_path(instance, filename):
        user_id = instance.post.user.id
        post_id = instance.post.id

        ext = os.path.splitext(filename)[1]  # .jpg, .png
        short_id = shortuuid.uuid()[:5]

        filename = f"{post_id}_{short_id}{ext}"

        return f"users/user_{user_id}/post_{post_id}/{filename}"

    image = models.ImageField(upload_to=gallery_upload_path)

class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to=user_directory_path)
    description = models.TextField(null=True, blank=True)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, choices=AVAILABILITY, default="available")
    
    pid = ShortUUIDField(length=7, max_length=25, alphabet='abcdefghijklmnopqrstuvwxyz')
    slug = models.SlugField(unique=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        uuid_key = shortuuid.uuid()
        uniqueid = uuid_key[:2]
        if self.slug == "" or self.slug == None:
            self.slug = slugify(self.title) + '-' + uniqueid
        super(Product, self).save(*args, **kwargs)

class RentalRequest(models.Model):
    rr_id = ShortUUIDField(length=7, max_length=25, alphabet='abcdefghijklmnopqrstuvwxyz')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_rental_requests")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="rental_requests")
    renter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rental_requests")
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=RENTAL_STATUS, default="Pending")
    handed_over = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    returned_confirmed = models.BooleanField(default=False)
    returned = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Rental Requests'

    def __str__(self):
        return f"Request for '{self.product.title}' by {self.renter.username}"

class Review(models.Model):
    # A OneToOneField ensures one review per rental request.
    rental_request = models.OneToOneField(RentalRequest, on_delete=models.CASCADE, related_name="review")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews_given")
    rating = models.IntegerField(default=0)
    comment = models.TextField(max_length=300)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Reviews'

    def __str__(self):
        return f"Review for '{self.product.title}' by {self.reviewer.username}"


class DisputeReport(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="dispute_reporter")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="disputed_product", null=True, blank=True)
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reported_user", null=True, blank=True)
    reason = models.CharField(max_length=100)
    description = models.TextField(max_length=200)
    status = models.CharField(max_length=20, choices=DISPUTE_STATUS, default="pending")
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Dispute Reports'

    def __str__(self):
        if self.product:
            return f"Report for product '{self.product.title}' by {self.reporter.username}"
        elif self.reported_user:
            return f"Report for user '{self.reported_user.username}' by {self.reporter.username}"
        return f"Report by {self.reporter.username}"


class SavedPost(Post):
    class Meta:
        proxy = True
        verbose_name = "Saved Post"
        verbose_name_plural = "Saved Posts"

class Gallery(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="gallery", null=True, blank=True)
    active = models.BooleanField(default=True)  
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self): #self means semua under class gallery
        return str(self.post) 

    class Meta:
        verbose_name_plural = 'Gallery'

    def thumbnail(self):
        return mark_safe('<img src="/media/%s" width="50" height="50" object-fit:"cover" style="border-radius: 5px;" />' % (self.image))

#define friend model
class Friend(models.Model):
    fid = ShortUUIDField(length=7, max_length=25, alphabet='abcdefghijklmnopqrstuvwxyz')
    #user - the one who adds the friend (one-directional)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user")
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friend")
    is_active = models.BooleanField(default=True)  # True=active friendship, False=unfriended (keeps history)
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} -> {self.friend.username}"

    class Meta:
        verbose_name_plural = 'Friend'
        unique_together = ('user', 'friend')  # Prevent duplicate friendships

#create comment model
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comment_user")
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    comment = models.CharField(max_length=1000)
    #content = models.TextField()
    active = models.BooleanField(default=True)  
    date = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, blank=True, related_name="comment_likes") #1 post: many likes
    cid = ShortUUIDField(length=7, max_length=25, alphabet='abcdefghijklmnopqrstuvwxyz')

    def __str__(self): #self means semua under class gallery
        return str(self.post) 

    class Meta:
        verbose_name_plural = 'Comment'

    def comment_replies(self):
        comment_replies = ReplyComment.objects.filter(comment=self, active=True) #get all active replies
        return comment_replies

#create reply comment model
class ReplyComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reply_user")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    reply = models.CharField(max_length=1000)
    likes = models.ManyToManyField(User, blank=True, related_name="reply_likes")
    #content = models.TextField()
    active = models.BooleanField(default=True)  
    date = models.DateTimeField(auto_now_add=True)
    cid = ShortUUIDField(length=7, max_length=25, alphabet='abcdefghijklmnopqrstuvwxyz')

    def __str__(self): #self means semua under class gallery
        return str(self.comment) 

    class Meta:
        verbose_name_plural = 'Reply Comment'

class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="sender_messages")
    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="receiver_messages")

    message = models.CharField(max_length=100000, null=True, blank=True)
    image = models.ImageField(upload_to="chat-images", null=True, blank=True)
    is_read = models.BooleanField(default=False)
    
    date = models.DateTimeField(auto_now_add=True)
    mid = ShortUUIDField(length=10, max_length=25, alphabet="abcdefghijklmnopqrstuvwxyz")
    
    rental_request = models.ForeignKey('RentalRequest', on_delete=models.SET_NULL, null=True, blank=True, related_name="chat_messages")
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True, related_name="chat_messages")
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('rental_card', 'Rental Card'),
    )
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')

    class Meta:
        ordering = ['date']
        verbose_name_plural = "Chat Messages"

    def __str__(self):
        sender_username = self.sender.username if self.sender else "Deleted User"
        receiver_username = self.receiver.username if self.receiver else "Deleted User"
        if self.message:
            return f"{sender_username} to {receiver_username} - {self.message[:20]}"
        else:
            return f"{sender_username} to {receiver_username} - [Image]"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notification_user")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notification_sender", null=True, blank=True)
    notification_type = models.CharField(max_length=100, choices=NOTIFICATION_TYPE)
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.SET_NULL, null=True, blank=True)
    dispute = models.ForeignKey(DisputeReport, on_delete=models.SET_NULL, null=True, blank=True)
    rental_request = models.ForeignKey(RentalRequest, on_delete=models.SET_NULL, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    nid = ShortUUIDField(length=7, max_length=25, alphabet='abcdefghijklmnopqrstuvwxyz')

    def __str__(self): #self means semua under class gallery
        return str(self.user) 

    class Meta:
        verbose_name_plural = 'Notification'