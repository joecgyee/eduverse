from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from apps.courses.models import Course, Enrollment, EnrollmentStatus

from .models import *
from .forms import *


@login_required
def chat_rooms_list_view(request):
    """
    Students see chat rooms for courses they're actively enrolled in.
    Teachers see chat rooms for courses they teach.
    """
    if request.user.is_teacher:
        rooms = ChatRoom.objects.filter(course__teacher=request.user).select_related("course")
    else:
        enrolled_course_ids = Enrollment.objects.filter(
            student=request.user, status=EnrollmentStatus.ACTIVE
        ).values_list("course_id", flat=True)
        rooms = ChatRoom.objects.filter(course_id__in=enrolled_course_ids).select_related("course")

    return render(request, "chat/chat_rooms_list.html", {"rooms": rooms})


@login_required
def chat_room_create_view(request, course_pk):
    """Creates a chat room for a course, teacher-only, and auto-joins the teacher."""
    course = get_object_or_404(Course, pk=course_pk)
    if course.teacher_id != request.user.id:
        raise PermissionDenied("You can only create chat rooms for your own courses.")

    room = ChatRoom.objects.create(course=course, created_by=request.user)
    ChatRoomMember.objects.create(room=room, user=request.user)

    # Auto-add all actively enrolled students.
    enrolled_students = Enrollment.objects.filter(
        course=course, status=EnrollmentStatus.ACTIVE
    ).values_list("student_id", flat=True)
    ChatRoomMember.objects.bulk_create([
        ChatRoomMember(room=room, user_id=student_id) for student_id in enrolled_students
    ])

    messages.success(request, "Chat room created.")
    return redirect("chat:room_detail", pk=room.pk)


@login_required
def chat_room_start_view(request):
    """Lets a student start a chat room for a course they're enrolled in."""
    if not request.user.is_student:
        raise PermissionDenied("Only students can use this to start a chat room. Teachers use their course page.")

    if request.method == "POST":
        form = ChatRoomCreateForm(request.POST, user=request.user)
        if form.is_valid():
            course = form.cleaned_data["course"]
            room = ChatRoom.objects.create(
                course=course,
                name=form.cleaned_data["name"] or None,
                created_by=request.user,
            )
            ChatRoomMember.objects.create(room=room, user=request.user)

            members_to_add = form.cleaned_data["members"]
            ChatRoomMember.objects.bulk_create([
                ChatRoomMember(room=room, user=member)
                for member in members_to_add
            ])

            messages.success(request, "Chat room created.")
            return redirect("chat:room_detail", pk=room.pk)
    else:
        form = ChatRoomCreateForm(user=request.user)

    return render(request, "chat/chat_room_start.html", {"form": form})


@login_required
def chat_room_detail_view(request, pk):
    room = get_object_or_404(ChatRoom, pk=pk)

    is_member = ChatRoomMember.objects.filter(room=room, user=request.user).exists()
    if not is_member:
        raise PermissionDenied("You are not a member of this chat room.")

    recent_messages = room.messages.select_related("sender").order_by("sent_at")[:50]
    members = room.members.select_related("user", "user__teacher_profile").order_by("user__first_name")

    return render(request, "chat/chat_room_detail.html", {
        "room": room,
        "recent_messages": recent_messages,
        "members": members,
    })


@login_required
def course_members_ajax_view(request, course_pk):
    """
    Returns {id, name} for everyone who shares this course with the current
    student (classmates + teacher), used to repopulate the 'Invite Members'
    dropdown when the course selection changes.
    """
    course = get_object_or_404(Course, pk=course_pk)

    is_enrolled = Enrollment.objects.filter(
        student=request.user, course=course, status=EnrollmentStatus.ACTIVE
    ).exists()
    if not is_enrolled:
        return JsonResponse({"members": []})

    classmates = Enrollment.objects.filter(
        course=course, status=EnrollmentStatus.ACTIVE
    ).exclude(student=request.user).select_related("student")

    members = [{"id": e.student.id, "name": e.student.get_full_name()} for e in classmates]
    members.append({"id": course.teacher.id, "name": f"{course.teacher.teacher_profile.title or ''} {course.teacher.get_full_name()}".strip()})

    return JsonResponse({"members": members})


@login_required
@require_POST
def chat_attachment_upload_view(request, pk):
    """
    Uploads a file attachment to a chat room via normal HTTP POST (not the
    websocket, which isn't suited for binary payloads), saves it as a
    ChatMessage, then broadcasts it to everyone in the room over the
    channel layer so it appears live, exactly like a text message would.
    """
    room = get_object_or_404(ChatRoom, pk=pk)

    is_member = ChatRoomMember.objects.filter(room=room, user=request.user).exists()
    if not is_member:
        raise PermissionDenied("You are not a member of this chat room.")

    form = ChatAttachmentForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)

    message = form.save(commit=False)
    message.room = room
    message.sender = request.user
    message.save()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{room.pk}",
        {
            "type": "chat_message",
            "message_id": message.id,
            "content": message.content,
            "attachment_url": message.attachment.url if message.attachment else None,
            "attachment_name": message.attachment.name.split("/")[-1] if message.attachment else None,
            "sender_id": request.user.id,
            "sender_name": request.user.get_full_name(),
            "sent_at": timezone.localtime(message.sent_at).strftime("%b %d, %Y %I:%M %p"),
        },
    )

    return JsonResponse({"status": "ok", "message_id": message.id})