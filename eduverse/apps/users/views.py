from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_protect

from .forms import *
from apps.feed.forms import FeedCommentForm

from django.db.models import Q

from apps.chat.models import ChatRoom
from apps.courses.models import Course, Enrollment, EnrollmentStatus
from apps.feed.models import Feed

@csrf_protect
def register_view(request):
    if request.user.is_authenticated:
        return redirect("users:dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created. Please log in.")
            return redirect("users:login")
    else:
        form = RegisterForm()

    return render(request, "users/register.html", {"form": form})


@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect("users:dashboard")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("username")  # field name stays 'username' internally
            password = form.cleaned_data.get("password")
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                next_url = request.GET.get("next", "users:dashboard")
                return redirect(next_url)
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm(request)

    return render(request, "users/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("/")


@login_required
def dashboard_view(request):
    user = request.user

    if user.is_teacher:
        courses = Course.objects.filter(teacher=user).order_by("-created_at")[:5]
    else:
        courses = Course.objects.filter(
            enrollments__student=user, enrollments__status=EnrollmentStatus.ACTIVE
        ).order_by("-enrollments__enrolled_at")[:5]

    recent_posts = Feed.objects.select_related("author").order_by("-created_at")[:5]

    recent_chats = ChatRoom.objects.filter(
        members__user=user
    ).select_related("course").order_by("-created_at")[:5]

    return render(request, "users/dashboard.html", {
        "courses": courses,
        "recent_posts": recent_posts,
        "recent_chats": recent_chats,
    })


@login_required
def user_search_view(request):
    query = request.GET.get("q", "").strip()
    results = []

    if query:
        results = User.objects.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        ).exclude(id=request.user.id).distinct()

    return render(request, "users/user_search_results.html", {"query": query, "results": results})


@login_required
def user_detail_view(request, pk=None):
    """
    No pk -> current user's own profile.
    pk provided -> viewing another user's public profile (read-only, no Edit button).
    """
    if pk is None:
        profile_user = request.user
    else:
        profile_user = get_object_or_404(User, pk=pk)

    is_own_profile = profile_user.id == request.user.id

    profile_feeds = profile_user.feed_posts.select_related("author").prefetch_related("comments__author")[:5]

    return render(request, "users/user_detail.html", {
        "profile_user": profile_user,
        "profile_feeds": profile_feeds,
        "comment_form": FeedCommentForm(),
        "is_own_profile": is_own_profile,
    })


@login_required
def user_update_view(request):
    user = request.user

    profile_form_class = StudentProfileUpdateForm if user.is_student else TeacherProfileUpdateForm
    profile_instance = user.student_profile if user.is_student else user.teacher_profile

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, request.FILES, instance=user)
        profile_form = profile_form_class(request.POST, instance=profile_instance)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("users:detail")
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = profile_form_class(instance=profile_instance)

    return render(
        request, "users/user_form.html",
        {"user_form": user_form, "profile_form": profile_form},
    )