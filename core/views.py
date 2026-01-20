from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.text import slugify
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils.timesince import timesince
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Max

from core.models import Post, Comment, ReplyComment, Friend, PostThumbnail, Product, DisputeReport, Notification, RentalRequest, Review, ChatMessage
from userauths.models import User
from datetime import datetime

import shortuuid

# Create your views here. all fx must return smth
@login_required
def index(request):
    #bring out all obj in db (show all active posts)
    posts = Post.objects.filter(active=True).order_by("-date")  #latest post on top

    # Suggested Users - exclude active friends
    user_following = Friend.objects.filter(user=request.user, is_active=True)
    following_list = [f.friend.id for f in user_following]
    following_list.append(request.user.id)

    suggested_users = User.objects.exclude(id__in=following_list).order_by('?')[:4]

    # Suggested Products
    suggested_products = Product.objects.exclude(user=request.user).order_by('?')[:4]

    # Get user's rental products for "Open for Rent" validation
    user_products = Product.objects.filter(user=request.user) if request.user.is_authenticated else []

    context = { "posts": posts, "suggested_users": suggested_users, "user_products": user_products, "suggested_products": suggested_products }
    return render(request, "core/index.html", context)

@login_required
def post_detail(request, slug):
    post = Post.objects.get(slug=slug, active=True)
    context = {"p":post}
    return render(request, "core/post-detail.html", context)

@login_required
def save_post(request):
    post_id = request.GET.get('id')
    if not post_id:
        return HttpResponseBadRequest("Missing 'id' parameter.")

    try:
        post = Post.objects.get(id=post_id)
    except (Post.DoesNotExist, ValueError):
        return HttpResponseBadRequest("Invalid post ID.")

    is_saved = False
    if request.user in post.saved.all():
        post.saved.remove(request.user)
        is_saved = False # Post is now unsaved
    else:
        post.saved.add(request.user)
        is_saved = True # Post is now saved
    return JsonResponse({'is_saved': is_saved})

@csrf_exempt
#if error change > @login_required
def create_post(request):
    if request.method == "POST":
        # Require a non-empty caption
        title = (request.POST.get("post-caption") or "").strip()
        if not title:
            return JsonResponse({"error": "Caption is required."}, status=400)

        visibility = request.POST.get("visibility")
        print("DEBUG create_post - received visibility:", repr(visibility))

        # Validate rental item when posting "Open for Rent"
        rental_item_pid = (request.POST.get("rental_item") or "").strip()
        if visibility == "Open for Rent":
            user_products = Product.objects.filter(user=request.user)
            if not user_products.exists():
                return JsonResponse({"error": "Add at least one rental item before posting as Open for Rent."}, status=400)
            if not rental_item_pid:
                return JsonResponse({"error": "Please select an item listing to rent out."}, status=400)
            # ensure the selected item belongs to the user
            try:
                user_products.get(pid=rental_item_pid)
            except Product.DoesNotExist:
                return JsonResponse({"error": "Selected item is invalid."}, status=400)

        images = request.FILES.getlist("post-thumbnail")

        uuid_key = shortuuid.uuid()
        uniqueid = uuid_key[:4]

        # Get selected product if "Open for Rent"
        selected_product = None
        if visibility == "Open for Rent" and rental_item_pid:
            try:
                selected_product = Product.objects.get(pid=rental_item_pid, user=request.user)
            except Product.DoesNotExist:
                pass

        post = Post.objects.create(
            title=title,
            visibility=visibility,
            user=request.user,
            slug=slugify(title) + "-" + uniqueid.lower(),
            product=selected_product
        )
        print("DEBUG create_post - saved post.visibility:", repr(post.visibility))

        for img in images:
            PostThumbnail.objects.create(
                post=post,
                image=img
            )

        image_urls = [img.image.url for img in post.post_thumbnail.all()]

        # Include product data if present
        product_data = None
        if post.product:
            product_data = {
                "title": post.product.title,
                "description": post.product.description,
                "daily_rate": str(post.product.daily_rate),
                "location": post.product.location,
                "image": post.product.image.url,
                "slug": post.product.slug,
                "pid": post.product.pid,
            }

        return JsonResponse({
            "post": {
                "title": post.title,
                "images": image_urls,   # 👈 multiple images
                "full_name": post.user.profile.full_name,
                "profile_image": post.user.profile.image.url,
                "date": timesince(post.date),
                "id": post.id,
                "visibility": post.visibility,
                "product": product_data,
            }
        })

    
def like_post(request):
    #send id of post yg kita like from frontend -> backend
    id = request.GET['id']  #dapat id dr frontend
    post = Post.objects.get(id=id)  #dapat post based on id atas ni
    user = request.user  #dapat logged in user
    bool = False 

    #check if user dah like post tu or belum
    if user in post.likes.all():
        post.likes.remove(user)
        bool = False #post is not liked
    else: #if user tk like post ?
        post.likes.add(user)
        bool = True
        
        # Create notification for post owner (only if not liking own post)
        if user != post.user:
            Notification.objects.create(
                user=post.user,
                sender=user,
                notification_type="New Like",
                post=post
            )

    #pass var to jsonresponse -> nk dpt real time update
    data = {
        "bool":bool,
        "likes":post.likes.all().count() #get count of likes
    }
    return JsonResponse({"data":data})

def comment_on_post(request):
    id = request.GET['id']
    comment = request.GET['comment']
    post = Post.objects.get(id=id) 
    comment_count = Comment.objects.filter(post=post).count() #kira existing comments
    user = request.user

    new_comment = Comment.objects.create(
        post = post,
        comment = comment,
        user = user 
    )
    
    # Create notification for post owner (only if not commenting on own post)
    if user != post.user:
        Notification.objects.create(
            user=post.user,
            sender=user,
            notification_type="New Comment",
            post=post,
            comment=new_comment
        )

    data = {
        "bool":True,
        "comment":new_comment.comment,
        "profile_image":new_comment.user.profile.image.url,
        "date":timesince(new_comment.date),
        "comment_id":new_comment.id,
        "post_id":new_comment.post.id,
        "post_slug":new_comment.post.slug, #for View All Comments link
        "comment_count":comment_count + int(1), #increment by 1
        "user_id":new_comment.user.id, #to check if comment belongs to logged in user
        "username":new_comment.user.username
    }
    return JsonResponse({"data":data})


def like_comment(request):
    id = request.GET['id']
    comment = Comment.objects.filter(id=id).first()
    user = request.user
    bool = False

    if user in comment.likes.all():
        comment.likes.remove(user) #remove user from from people yg like comment
        bool = False 
    else: #comment not like yet
        comment.likes.add(user)
        bool = True #comment has been liked
        
        # Create notification for comment owner (only if not liking own comment)
        if user != comment.user:
            Notification.objects.create(
                user=comment.user,
                sender=user,
                notification_type="Comment Liked",
                post=comment.post,
                comment=comment
            )

    data = {
        "bool":bool,
        "likes":comment.likes.all().count()
    }
    return JsonResponse({"data":data})

def like_reply(request):
    id = request.GET['id']
    reply = ReplyComment.objects.filter(id=id).first()
    user = request.user
    bool = False

    if user in reply.likes.all():
        reply.likes.remove(user)
        bool = False 
    else:
        reply.likes.add(user)
        bool = True
        
        # Create notification for reply owner (only if not liking own reply)
        if user != reply.user:
            Notification.objects.create(
                user=reply.user,
                sender=user,
                notification_type="Comment Liked",
                post=reply.comment.post,
                comment=reply.comment
            )

    data = {
        "bool":bool,
        "likes":reply.likes.all().count()
    }
    return JsonResponse({"data":data})

def reply_comment(request):
    id = request.GET['id']
    reply = request.GET['reply'].strip()

    # Validate that reply is not empty
    if not reply:
        return JsonResponse({"error": "Reply text cannot be empty"})

    comment = Comment.objects.get(id=id)
    user = request.user

    new_reply = ReplyComment.objects.create(
        comment = comment,
        reply = reply,
        user = user
    )
    
    # Create notification for comment owner (only if not replying to own comment)
    if user != comment.user:
        Notification.objects.create(
            user=comment.user,
            sender=user,
            notification_type="Comment Replied",
            post=comment.post,
            comment=comment
        )

    data = {
        "bool":True,
        "reply":new_reply.reply,
        "profile_image":new_reply.user.profile.image.url,
        "date":timesince(new_reply.date),
        "reply_id":new_reply.id,
        "post_id":new_reply.comment.post.id
    }
    return JsonResponse({"data":data})

def delete_comment(request):
    id = request.GET['id']
    comment = Comment.objects.get(id=id)
    post_id = comment.post.id  # Get post_id before deleting
    comment.delete()

    data = {
        "bool":True,
        "post_id":post_id
    }
    return JsonResponse({"data":data})

def delete_reply(request):
    id = request.GET['id']
    reply = ReplyComment.objects.get(id=id)
    comment_id = reply.comment.id  # Get comment_id before deleting
    reply.delete()

    data = {
        "bool":True,
        "comment_id":comment_id
    }
    return JsonResponse({"data":data})

@login_required
def delete_post(request):
    # Expect POST request with 'id' of post to delete
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=400)

    post_id = request.POST.get('id')
    if not post_id:
        return JsonResponse({'error': "Missing 'id' parameter."}, status=400)

    try:
        post = Post.objects.get(id=post_id)
    except (Post.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Invalid post ID.'}, status=404)

    # Only post owner can delete
    if post.user != request.user:
        return JsonResponse({'error': 'Unauthorized. You can only delete your own posts.'}, status=403)

    post.delete()
    return JsonResponse({'success': True, 'post_id': post_id})

@login_required
def add_friend(request):
    sender = request.user
    receiver_id = request.GET.get('id')

    if not receiver_id:
        return JsonResponse({"error": "Invalid request"})

    if sender.id == int(receiver_id):
        return JsonResponse({"error": "You cannot add yourself as a friend"})

    receiver = User.objects.get(id=receiver_id)

    # Check if active friendship already exists
    existing_friend = Friend.objects.filter(user=sender, friend=receiver, is_active=True).first()
    if existing_friend:
        return JsonResponse({"error": "You are already friends with this user"})

    # Check if there's an inactive friendship (re-activating)
    inactive_friend = Friend.objects.filter(user=sender, friend=receiver, is_active=False).first()
    if inactive_friend:
        inactive_friend.is_active = True
        inactive_friend.save()
    else:
        # Create new friendship (one-directional)
        Friend.objects.create(user=sender, friend=receiver, is_active=True)
    
    # Create notification for receiver
    Notification.objects.create(
        user=receiver,
        sender=sender,
        notification_type="Friend Added"
    )
    
    return JsonResponse({"success": "Friend added", "bool": True})

# Accept and decline friend request views removed - no longer needed with direct friend addition

@login_required
def unfriend(request):
    friend_id = request.GET.get('id')
    
    if not friend_id:
        return JsonResponse({"error": "Invalid request"})
    
    user = request.user
    friend_user = User.objects.get(id=friend_id)
    
    try:
        # Set friendship to inactive (one-directional, keeps history)
        friend = Friend.objects.filter(user=user, friend=friend_user, is_active=True).first()
        
        if friend:
            friend.is_active = False
            friend.save()
            return JsonResponse({"success": "Unfriended", "bool": False})
        else:
            return JsonResponse({"error": "Friendship not found"})
        
    except Exception as e:
        return JsonResponse({"error": str(e)})
    
@login_required
def messages_view(request):
    user = request.user
    chat_with_user_id = request.GET.get('user_id')

    # Get all users the current user has had a conversation with
    sent_to_ids = ChatMessage.objects.filter(sender=user).values_list('receiver_id', flat=True)
    received_from_ids = ChatMessage.objects.filter(receiver=user).values_list('sender_id', flat=True)
    other_user_ids = set(list(sent_to_ids) + list(received_from_ids))

    # If we are starting a new chat from a profile, add the user to the set
    active_chat_user = None
    if chat_with_user_id:
        try:
            active_chat_user = User.objects.get(id=chat_with_user_id)
            if active_chat_user.id != user.id:
                other_user_ids.add(active_chat_user.id)
        except (User.DoesNotExist, ValueError, TypeError):
            active_chat_user = None

    conversations = []
    for user_id_loop in other_user_ids:
        try:
            other_user = User.objects.get(id=user_id_loop)
        except User.DoesNotExist:
            continue
        
        # Get the last message in the conversation
        try:
            last_message = ChatMessage.objects.filter(
                (Q(sender=user, receiver=other_user) | Q(sender=other_user, receiver=user))
            ).latest('date')
        except ChatMessage.DoesNotExist:
            last_message = None

        # Get the count of unread messages from this user
        unread_count = ChatMessage.objects.filter(
            sender=other_user, receiver=user, is_read=False
        ).count()

        conversations.append({'user': other_user, 'last_message': last_message, 'unread_count': unread_count})

    # Sort conversations by the date of the last message
    conversations.sort(key=lambda x: x['last_message'].date if x['last_message'] else timezone.now(), reverse=True)

    # Handle Draft Product for Chat
    draft_product = None
    product_id = request.GET.get('product_id')
    if product_id:
        try:
            draft_product = Product.objects.get(pid=product_id)
        except Product.DoesNotExist:
            pass

    context = {
        "conversations": conversations,
        "active_chat_user": active_chat_user,
        "draft_product": draft_product
    }
    return render(request, "core/messages.html", context)

@login_required
def start_rental_chat(request, rr_id):
    rental_request = get_object_or_404(RentalRequest, rr_id=rr_id)
    action_type = request.GET.get('type')
    
    target_user = None
    message_text = ""
    
    if action_type == "handover":
        if request.user != rental_request.owner:
             messages.error(request, "Unauthorized.")
             return redirect("core:feed")
        target_user = rental_request.renter
        message_text = "Thank you for your payment. I'd like to hand over this item. When are you available?"
        
    elif action_type == "return":
        if request.user != rental_request.renter:
             messages.error(request, "Unauthorized.")
             return redirect("core:feed")
        target_user = rental_request.owner
        message_text = "I have done renting this item. I'd like to return this item. When are you available?"
    
    else:
        messages.error(request, "Invalid action.")
        return redirect("core:feed")

    # Prevent duplicate auto-messages for the same rental phase
    existing_message = ChatMessage.objects.filter(
        sender=request.user,
        receiver=target_user,
        rental_request=rental_request,
        message=message_text,
        message_type='rental_card'
    ).exists()

    if not existing_message:
        ChatMessage.objects.create(
            sender=request.user,
            receiver=target_user,
            message=message_text,
            rental_request=rental_request,
            message_type='rental_card',
            is_read=False
        )
    
    return redirect(f"{reverse('core:messages')}?user_id={target_user.id}")

@login_required
def get_messages_api(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    # Mark messages as read
    ChatMessage.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)
    
    messages = ChatMessage.objects.filter(
        (Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user))
    ).order_by('date')
    
    message_list = []
    for message in messages:
        msg_data = {
            'id': message.id,
            'sender_id': message.sender.id,
            'message': message.message,
            'image': message.image.url if message.image else None,
            'is_read': message.is_read,
            'date': timesince(message.date) + " ago",
            'message_type': message.message_type,
            'rental_request': None,
            'product': None
        }
        
        if message.rental_request:
            msg_data['rental_request'] = {
                'title': message.rental_request.product.title,
                'image': message.rental_request.product.image.url,
                'start_date': message.rental_request.start_date.strftime('%b %d, %Y'),
                'end_date': message.rental_request.end_date.strftime('%b %d, %Y'),
                'total_price': str(message.rental_request.total_price),
                'slug': message.rental_request.product.slug
            }
        
        if message.product:
            msg_data['product'] = {
                'title': message.product.title,
                'image': message.product.image.url,
                'daily_rate': str(message.product.daily_rate),
                'slug': message.product.slug
            }
        message_list.append(msg_data)
        
    return JsonResponse({"messages": message_list})

@login_required
def send_message_api(request):
    if request.method == 'POST':
        receiver_id = request.POST.get('receiver_id')
        message_content = request.POST.get('message')
        image = request.FILES.get('image')
        product_id = request.POST.get('product_id')

        if not receiver_id or (not message_content and not image and not product_id):
            return JsonResponse({'error': 'Missing data'}, status=400)

        receiver = get_object_or_404(User, id=receiver_id)
        product = None
        if product_id:
            product = get_object_or_404(Product, pid=product_id)

        chat_message = ChatMessage.objects.create(sender=request.user, receiver=receiver, message=message_content, image=image, product=product)

        msg_data = {
            'id': chat_message.id,
            'sender_id': chat_message.sender.id,
            'message': chat_message.message,
            'image': chat_message.image.url if chat_message.image else None,
            'is_read': chat_message.is_read,
            'date': timesince(chat_message.date) + " ago",
            'message_type': chat_message.message_type,
            'product': None
        }

        if chat_message.product:
            msg_data['product'] = {
                'title': chat_message.product.title,
                'image': chat_message.product.image.url,
                'daily_rate': str(chat_message.product.daily_rate),
                'slug': chat_message.product.slug
            }

        return JsonResponse({'message': msg_data})
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def add_item(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        daily_rate = request.POST.get("daily_rate")
        location = request.POST.get("location")
        image = request.FILES.get("image")

        Product.objects.create(
            user=request.user,
            title=title,
            description=description,
            daily_rate=daily_rate,
            location=location,
            image=image,
        )
        
        messages.success(request, "Item added successfully!")
        return redirect(request.META.get('HTTP_REFERER', 'core:feed'))
    return redirect("core:feed")

@login_required
def item_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    context = {
        "product": product,
    }
    return render(request, "core/item-details.html", context)

@login_required
def edit_item(request, pid):
    # Ensure the user editing is the owner of the item
    product = get_object_or_404(Product, pid=pid, user=request.user)

    if product.status == 'rented':
        messages.error(request, "This item is currently rented and cannot be edited.")
        return redirect(request.META.get('HTTP_REFERER', 'userauths:my-profile'))

    if request.method == "POST":
        product.title = request.POST.get("title")
        product.description = request.POST.get("description")
        product.daily_rate = request.POST.get("daily_rate")
        product.location = request.POST.get("location")
        
        new_status = request.POST.get("status")
        if new_status == 'rented':
            messages.error(request, "Invalid status update. 'Rented' status is system-controlled.")
            return redirect(request.META.get('HTTP_REFERER', 'userauths:my-profile'))
        
        if new_status in ['available', 'unavailable']:
            product.status = new_status
        
        if request.FILES.get("image"):
            product.image = request.FILES.get("image")
            
        product.save()
        messages.success(request, "Item updated successfully!")
        return redirect(request.META.get('HTTP_REFERER', 'core:feed'))
    
    return redirect("userauths:my-profile")

@login_required
def delete_item(request, pid):
    # Ensure the user deleting is the owner of the item
    product = get_object_or_404(Product, pid=pid, user=request.user)

    if request.method == "POST":
        product.delete()
        return JsonResponse({'status': 'success', 'message': 'Item deleted successfully.'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

@login_required
def create_rental_request(request):
    if request.method == "POST":
        product_pid = request.POST.get("product_pid")
        start_date_str = request.POST.get("start_date")
        end_date_str = request.POST.get("end_date")
        total_days = request.POST.get("total_days")
        total_price = request.POST.get("total_price")

        product = get_object_or_404(Product, pid=product_pid)
        renter = request.user

        if product.user == renter:
            return JsonResponse({"status": "error", "message": "You cannot rent your own item."}, status=400)

        # Convert date strings to date objects
        start_date = datetime.strptime(start_date_str, '%m/%d/%Y').date()
        end_date = datetime.strptime(end_date_str, '%m/%d/%Y').date()

        # Create RentalRequest
        rental_request = RentalRequest.objects.create(
            owner=product.user,
            product=product,
            renter=renter,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            total_price=total_price,
            status="Pending"
        )

        # Create Notification for owner
        Notification.objects.create(
            user=product.user,
            sender=renter,
            notification_type="Rental Request",
            rental_request=rental_request
        )

        return JsonResponse({"status": "success", "message": "Your request has been sent to the owner. Please wait for approval."})

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=400)

@login_required
def manage_rental_request(request):
    if request.method == "POST":
        request_id = request.POST.get("request_id")
        action = request.POST.get("action")

        rental_request = get_object_or_404(RentalRequest, rr_id=request_id)
        
        # Permission check
        if request.user != rental_request.owner and request.user != rental_request.renter:
            return JsonResponse({"status": "error", "message": "Unauthorized action."}, status=403)

        if action == "approve" and rental_request.status == "Pending" and request.user == rental_request.owner:
            rental_request.status = "Approved"
            rental_request.approved_at = timezone.now()
            rental_request.save()
            # Create notification for renter
            Notification.objects.create(
                user=rental_request.renter,
                sender=request.user,
                notification_type="Rental Request Approved",
                rental_request=rental_request
            )
            return JsonResponse({"status": "success", "new_status": "Approved"})

        elif action == "decline" and rental_request.status == "Pending" and request.user == rental_request.owner:
            rental_request.status = "Declined"
            rental_request.save()
            # Create notification for renter
            Notification.objects.create(
                user=rental_request.renter,
                sender=request.user,
                notification_type="Rental Request Declined",
                rental_request=rental_request
            )
            return JsonResponse({"status": "success", "new_status": "Declined"})

        elif action == "handed_over" and rental_request.status == "Paid" and request.user == rental_request.owner:
            rental_request.handed_over = True
            # Note: We do NOT transition to "Ongoing" here anymore. 
            # Transition happens only after Renter confirms receipt.
            rental_request.save()
            
            # Notify renter
            Notification.objects.create(
                user=rental_request.renter,
                sender=request.user,
                notification_type="Item Handed Over",
                rental_request=rental_request
            )
            return JsonResponse({"status": "success", "new_status": rental_request.status})

        elif action == "received" and rental_request.status == "Paid" and request.user == rental_request.renter:
            if not rental_request.handed_over:
                return JsonResponse({"status": "error", "message": "Owner has not handed over the item yet."}, status=400)
            
            rental_request.received = True
            
            # Check if start_date is reached (allow 1 day buffer for timezone differences)
            if timezone.now().date() >= rental_request.start_date - timedelta(days=1):
                rental_request.status = "Ongoing"
                product = rental_request.product
                product.status = "rented"
                product.save()
            
            rental_request.save()
            
            # Notify owner
            Notification.objects.create(
                user=rental_request.owner,
                sender=request.user,
                notification_type="Item Received",
                rental_request=rental_request
            )
            return JsonResponse({"status": "success", "new_status": rental_request.status})

        elif action == "returned" and rental_request.status == "Ongoing" and request.user == rental_request.owner:
            if not rental_request.returned_confirmed:
                 return JsonResponse({"status": "error", "message": "Renter has not confirmed the return yet."}, status=400)

            rental_request.returned = True
            rental_request.status = "Completed"
            product = rental_request.product
            product.status = "available"
            product.save()
            rental_request.save()
            
            # Notify renter
            Notification.objects.create(
                user=rental_request.renter,
                sender=request.user,
                notification_type="Rental Completed",
                rental_request=rental_request
            )
            return JsonResponse({"status": "success", "new_status": "Completed"})
        
        elif action == "returned_confirmed" and rental_request.status == "Ongoing" and request.user == rental_request.renter:
            rental_request.returned_confirmed = True
            rental_request.save()
            
            # Notify owner
            Notification.objects.create(
                user=rental_request.owner,
                sender=request.user,
                notification_type="Item Returned",
                rental_request=rental_request
            )
            return JsonResponse({"status": "success", "new_status": "Ongoing"})

        elif action == "complete" and rental_request.status == "Ongoing":
            rental_request.status = "Completed"
            rental_request.save()
            return JsonResponse({"status": "success", "new_status": "Completed"})

        return JsonResponse({"status": "error", "message": "Invalid action or request status."}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=400)

def _cancel_expired_requests():
    """
    Finds and cancels approved rental requests that have not been paid within 12 hours.
    This is a helper function called by various views to ensure statuses are up-to-date.
    """
    twelve_hours_ago = timezone.now() - timedelta(hours=12)
    
    # Find requests that were approved more than 12 hours ago and are still in 'Approved' status
    expired_requests = RentalRequest.objects.filter(
        status='Approved',
        approved_at__lt=twelve_hours_ago
    )

    for req in expired_requests:
        req.status = 'Cancelled'
        req.save()

        # Notify the renter (no sender, as it's a system action)
        Notification.objects.create(
            user=req.renter,
            notification_type="Rental Request Cancelled",
            rental_request=req
        )
        # Notify the owner
        Notification.objects.create(
            user=req.owner,
            notification_type="Rental Request Cancelled",
            rental_request=req
        )

def _update_ongoing_rentals():
    """
    Finds paid and handed-over rentals that have reached their start date
    and updates their status to 'Ongoing'. Now also requires 'received' confirmation.
    """
    today = timezone.localtime(timezone.now()).date()
    # Find requests that are 'Paid', have been handed over AND received, and their start date is today or in the past.
    requests_to_start = RentalRequest.objects.filter(
        status='Paid',
        handed_over=True,
        received=True,
        start_date__lte=today
    )
    for req in requests_to_start:
        req.status = 'Ongoing'
        product = req.product
        product.status = "rented"
        product.save()
        req.save()

def _notify_rental_end():
    """
    Finds ongoing rentals that have passed their end date and notifies the renter.
    """
    today = timezone.now().date()
    # Find rentals that are ongoing but the end date is in the past
    expired_rentals = RentalRequest.objects.filter(
        status='Ongoing',
        end_date__lt=today
    )

    for req in expired_rentals:
        # Check if notification already sent to avoid duplicates
        if not Notification.objects.filter(rental_request=req, notification_type="Rental Period Ended").exists():
            Notification.objects.create(
                user=req.renter,
                sender=req.owner,
                notification_type="Rental Period Ended",
                rental_request=req
            )

@login_required
def submit_report(request):
    if request.method == "POST":
        product_pid = request.POST.get("product_pid")
        reason = request.POST.get("reason")
        description = request.POST.get("description")

        product = get_object_or_404(Product, pid=product_pid)
        reporter = request.user

        # Create the dispute report
        dispute = DisputeReport.objects.create(
            reporter=reporter,
            product=product,
            reason=reason,
            description=description
        )

        # Create a notification for the product owner
        if product.user != reporter:
            Notification.objects.create(
                user=product.user,
                sender=reporter,
                notification_type="Dispute Report",
                dispute=dispute
            )

        return JsonResponse({"status": "success", "message": "Report submitted successfully."})
    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=400)

@login_required
def notification_list(request):
    _cancel_expired_requests()
    _notify_rental_end()
    _update_ongoing_rentals()
    notifications = Notification.objects.filter(user=request.user).order_by("-date")
    
    # Mark all notifications as read EXCEPT pending Friend Request notifications
    # Keep "Friend Request" unread until user acts on it
    # But mark "Friend Request Accepted By Me" and "Friend Request Declined By Me" as read
    notifications.exclude(notification_type="Friend Request").update(is_read=True)

    context = {"notifications": notifications}
    return render(request, "core/notifications.html", context)

@login_required
def submit_user_report(request):
    if request.method == "POST":
        reported_user_id = request.POST.get("reported_user_id")
        reason = request.POST.get("reason")
        description = request.POST.get("description")

        reported_user = get_object_or_404(User, id=reported_user_id)
        reporter = request.user

        if reporter == reported_user:
             return JsonResponse({"status": "error", "message": "You cannot report yourself."}, status=400)

        # Create the dispute report for a user
        dispute = DisputeReport.objects.create(
            reporter=reporter,
            reported_user=reported_user,
            reason=reason,
            description=description
        )

        # Create a notification for the reported user
        if reported_user != reporter:
            Notification.objects.create(
                user=reported_user,
                sender=reporter,
                notification_type="Dispute Report",
                dispute=dispute
            )

        return JsonResponse({"status": "success", "message": "Report submitted successfully."})
    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=400)

@login_required
def rental_progress(request):
    _cancel_expired_requests()
    _update_ongoing_rentals()
    _notify_rental_end()
    rental_requests = RentalRequest.objects.filter(owner=request.user).order_by("-date")
    context = {
        "rental_requests": rental_requests
    }
    return render(request, "core/rental-progress.html", context)

@login_required
def my_rental(request):
    _cancel_expired_requests()
    _update_ongoing_rentals()
    _notify_rental_end()
    rental_requests = RentalRequest.objects.filter(renter=request.user).order_by("-date")
    context = {
        "rental_requests": rental_requests
    }
    return render(request, "core/my-rental.html", context)

@login_required
def invoice_view(request, rr_id):
    _cancel_expired_requests()
    _update_ongoing_rentals()
    _notify_rental_end()
    rental_request = get_object_or_404(RentalRequest, rr_id=rr_id)

    # Ensure only the renter or owner can view the invoice
    if request.user != rental_request.renter and request.user != rental_request.owner:
        messages.error(request, "You do not have permission to view this invoice.")
        return redirect("core:feed")

    context = {
        "rental_request": rental_request
    }
    return render(request, "core/invoice.html", context)

@login_required
def confirm_payment(request, rr_id):
    if request.method == "POST":
        rental_request = get_object_or_404(RentalRequest, rr_id=rr_id, renter=request.user)

        if rental_request.status == "Approved":
            rental_request.status = "Paid"
            rental_request.paid_at = timezone.now()
            rental_request.save()

            # Notify owner
            Notification.objects.create(
                user=rental_request.owner,
                sender=request.user,
                notification_type="Payment Completed",
                rental_request=rental_request
            )

            return JsonResponse({"status": "success", "message": "Payment successful. Please wait for the owner to hand over the item."})
        else:
            return JsonResponse({"status": "error", "message": "This rental cannot be paid for at this time."}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=400)

@login_required
def submit_review(request, rr_id):
    rental_request = get_object_or_404(RentalRequest, rr_id=rr_id)

    # Security checks
    if rental_request.renter != request.user:
        messages.error(request, "You are not authorized to review this rental.")
        return redirect("core:my-rental")

    if rental_request.status != "Completed":
        messages.error(request, "You can only review completed rentals.")
        return redirect("core:my-rental")

    if hasattr(rental_request, 'review'):
        messages.error(request, "You have already reviewed this rental.")
        return redirect("core:my-rental")

    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment", "").strip()

        if not rating or not comment:
            messages.error(request, "Rating and comment are required.")
            return redirect(request.META.get('HTTP_REFERER', 'core:my-rental'))

        Review.objects.create(
            rental_request=rental_request,
            product=rental_request.product,
            reviewer=request.user,
            rating=int(rating),
            comment=comment
        )

        messages.success(request, "Thank you for your review!")
        return redirect("core:my-rental")

    # This view is for POST only, redirect if accessed via GET
    return redirect("core:my-rental")

@login_required
def search(request):
    query = request.GET.get("q")
    if query:
        users = User.objects.filter(Q(username__icontains=query) | Q(profile__full_name__icontains=query)).distinct()
        products = Product.objects.filter(Q(title__icontains=query)) # | Q(description__icontains=query) | Q(location__icontains=query)
    else:
        users = User.objects.none()
        products = Product.objects.none()

    context = {
        "users": users,
        "products": products,
        "query": query,
    }
    return render(request, "core/search.html", context)

@login_required
def my_listings(request):
    products = Product.objects.filter(user=request.user).order_by("-date")
    context = {
        "products": products,
    }
    return render(request, "core/my-listings.html", context)
