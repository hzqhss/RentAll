from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.core.mail import EmailMessage
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str, force_bytes

from django.conf import settings
from django.db import transaction
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages #django way of sending alert
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.http import HttpResponseRedirect

from core.models import Post, Product, Friend
from userauths.forms import UserRegisterForm, ProfileUpdateForm
from userauths.models import Profile, User
from userauths.tokens import email_verification_token

# Create your views here.
#ada email verification
def RegisterView(request):
    # If user is already logged in
    if request.user.is_authenticated:
        messages.warning(request, "You are already registered.")
        return redirect("core:feed")

    form = UserRegisterForm(request.POST or None)

    if form.is_valid():
        try:
            with transaction.atomic():
                # 1. Create inactive user
                user = form.save(commit=False)
                user.is_active = False
                user.save()  # temporary save inside transaction

                # 2. Extract cleaned data
                full_name = form.cleaned_data.get("full_name")
                phone = form.cleaned_data.get("phone")
                profile = Profile.objects.get(user=user)
                profile.full_name = full_name
                profile.phone = phone
                profile.save()

                # 3. Build verification email
                current_site = get_current_site(request)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = email_verification_token.make_token(user)

                verify_url = reverse(
                    "userauths:verify-email",
                    kwargs={"uidb64": uid, "token": token}
                )
                
                domain = "172.20.10.3:8000" #guna domain server sendiri
                protocol = "http" if settings.DEBUG else "https"

                email_body = (
                    f"Hi {profile.full_name},\n\n"
                    f"Please verify your RentAll account by clicking the link below:\n\n"
                    f"{protocol}://{domain}{verify_url}\n\n"
                    f"If you did not register, please ignore this email."
                )

                # 5. Send email
                EmailMessage(
                    subject="Verify your RentAll account",
                    body=email_body,
                    to=[user.email],
                ).send()

            # Runs ONLY if everything above succeeds
            messages.success(request,"Account created successfully! Please check your email to verify your account.")
            return redirect("userauths:sign-up")

        except Exception as e:
            # FULL rollback happens here
            messages.error(request, f"Registration failed: {e}")

    return render(request, "userauths/sign-up.html", {"form": form})

#tak dak email verification
# def RegisterView(request):
    # If user is already logged in
    if request.user.is_authenticated:
        messages.warning(request, "You are already registered.")
        return redirect("core:feed")

    form = UserRegisterForm(request.POST or None)

    if form.is_valid():
        try:
            with transaction.atomic():
                # Save user
                user = form.save()

                # Get extra fields
                full_name = form.cleaned_data.get("full_name")
                phone = form.cleaned_data.get("phone")
                email = form.cleaned_data.get("email")
                password = form.cleaned_data.get("password1")

                # Update profile
                profile = Profile.objects.get(user=user)
                profile.full_name = full_name
                profile.phone = phone
                profile.save()

                # Optional: auto login after register
                user = authenticate(request, email=email, password=password)
                if user is not None:
                    login(request, user)

            messages.success(
                request,
                f"Hi {full_name}, your account has been created successfully."
            )
            return redirect("core:feed")

        except Exception as e:
            messages.error(request, f"Registration failed: {e}")

    context = {"form": form}
    return render(request, "userauths/sign-up.html", context)



    # #return it back to feed page
    # messages.success(request, f"Hi {full_name}. Your account has been created successfully")
    # return redirect("core:feed")
    
    # context = {"form":form} #pass in the key value pair --> value = form
    # return render(request, "userauths/sign-up.html", context)

def VerifyEmail(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user and email_verification_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Email verified successfully. You may log in now.")
        return redirect("userauths:sign-in")
    else:
        messages.error(request, "Verification link is invalid or expired.")
        return redirect("userauths:sign-up")


def LoginView(request):
    if request.user.is_authenticated:
        messages.warning(request, "You are already logged in!")
        return redirect("core:feed")
    
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        try: #check if user exist
            user = User.objects.get(email=email)
            user = authenticate(request, email=email, password=password)

            if user is not None: #means user exists
                login(request, user)
                messages.success(request, "You are logged in!")
                return redirect("core:feed")
            else:
                messages.error(request, "Please verify your email before logging in.")
                return redirect("userauths:sign-up")

        except: #kalau user tak wujud
            messages.error(request, "User does not exist")
            return redirect("userauths:sign-up")

    return HttpResponseRedirect("/")

#request ni ada semua user data (username, pass, etc)
def LogoutView(request): #xboleh call logout sbb dh import package named logout
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("userauths:sign-up")

#profile view
@login_required
def my_profile(request):
    profile = request.user.profile
    # Split user's posts by visibility
    # Timeline should include both General and Open for Rent posts
    general_posts = Post.objects.filter(active=True, user=request.user, visibility__in=["General", "Open for Rent"]).order_by("-id")
    looking_posts = Post.objects.filter(active=True, user=request.user, visibility="Looking to Rent").order_by("-id")
    saved_posts = request.user.saved.all().order_by("-date")
    products = Product.objects.filter(user=request.user).order_by("-date")
    
    # Get user's friends with their friend counts (only active friendships)
    friends_queryset = Friend.objects.filter(user=request.user, is_active=True).select_related('friend__profile')[:6]
    friends_with_counts = []
    for friend_obj in friends_queryset:
        friend_count_for_user = Friend.objects.filter(user=friend_obj.friend, is_active=True).count()
        friends_with_counts.append({
            'friend_obj': friend_obj,
            'friend_count': friend_count_for_user
        })
    
    friend_count = Friend.objects.filter(user=request.user, is_active=True).count()

    context = {
        "profile": profile,
        "general_posts": general_posts,
        "looking_posts": looking_posts,
        "saved_posts": saved_posts, #Add the saved posts to context
        "products": products,
        "friends": friends_with_counts,
        "friend_count": friend_count,
    }

    return render(request, "userauths/my-profile.html", context)  

#friend profile view
@login_required
def friend_profile(request, username):
    profile = Profile.objects.get(user__username=username) #field lookup in django
    # Provide separate querysets for the friend profile page so the template can render both sections
    general_posts = Post.objects.filter(active=True, user=profile.user, visibility__in=["General", "Open for Rent"]).order_by("-id")
    looking_posts = Post.objects.filter(active=True, user=profile.user, visibility="Looking to Rent").order_by("-id")
    posts = Post.objects.filter(active=True, user=profile.user).order_by("-id")
    products = Product.objects.filter(user=profile.user).order_by("-date")

    sender = request.user
    receiver = profile.user #whoever owns the profile w the username 

    # Check if they are already friends (active friendship)
    bool_friend = Friend.objects.filter(user=sender, friend=receiver, is_active=True).exists()
    
    # Get profile user's friends with their friend counts (only active friendships)
    friends_queryset = Friend.objects.filter(user=profile.user, is_active=True).select_related('friend__profile')[:6]
    friends_with_counts = []
    for friend_obj in friends_queryset:
        friend_count_for_user = Friend.objects.filter(user=friend_obj.friend, is_active=True).count()
        friends_with_counts.append({
            'friend_obj': friend_obj,
            'friend_count': friend_count_for_user
        })
    
    friend_count = Friend.objects.filter(user=profile.user, is_active=True).count()

    context = {
        "profile": profile,
        "posts": posts,
        "general_posts": general_posts,
        "looking_posts": looking_posts,
        "bool_friend": bool_friend,
        "products": products,
        "friends": friends_with_counts,
        "friend_count": friend_count,
    }

    return render(request, "userauths/friend-profile.html", context)

@login_required
def settings_view(request):
    user = request.user
    profile = request.user.profile

    if request.method == "POST":
        # Check which form was submitted
        if 'update_profile' in request.POST:
            profile_form = ProfileUpdateForm(request.POST, instance=profile, user=user)
            password_form = PasswordChangeForm(user)  # Keep other form unbound

            if profile_form.is_valid():
                new_username = profile_form.cleaned_data.get('username')
                user.username = new_username
                # Sync User model fields with Profile fields
                user.full_name = profile_form.cleaned_data.get('full_name')
                user.phone = profile_form.cleaned_data.get('phone')
                user.gender = profile_form.cleaned_data.get('gender')
                user.save()

                profile_form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('userauths:settings')

        elif 'change_password' in request.POST:
            profile_form = ProfileUpdateForm(instance=profile, user=user, initial={'username': user.username, 'email': user.email, 'full_name': user.full_name})
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Important to keep the user logged in
                messages.success(request, 'Your password was successfully updated!')
                return redirect('userauths:settings')

    else:  # GET request
        profile_form = ProfileUpdateForm(instance=profile, user=user, initial={
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name
        })
        password_form = PasswordChangeForm(user)

    password_form.fields['old_password'].widget.attrs.update({'class': 'with-border'})
    password_form.fields['new_password1'].widget.attrs.update({'class': 'with-border'})
    password_form.fields['new_password2'].widget.attrs.update({'class': 'with-border'})

    context = {
        "profile_form": profile_form,
        "password_form": password_form,
    }
    return render(request, "userauths/settings.html", context)

@login_required
def edit_profile(request):
    if request.method == "POST":
        image = request.FILES.get("image")
        cover_image = request.FILES.get("cover_image")
        bio = request.POST.get("bio")
        profile = request.user.profile
        
        if image:
            profile.image = image
        if cover_image:
            profile.cover_image = cover_image
        if bio is not None:
            profile.bio = bio
            
        profile.save()
        messages.success(request, "Profile updated successfully")
        return redirect("userauths:my-profile")
    return redirect("userauths:my-profile")
