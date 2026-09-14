from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.courses.models import Course, Enrollment, EnrollmentStatus

from .models import ChatRoom, ChatRoomMember


@receiver(post_save, sender=Course)
def create_chat_room_for_course(sender, instance, created, **kwargs):
    """
    Auto-creates one chat room per course when the course is first created.
    The teacher is added as a member (and as created_by).
    """
    if not created:
        return

    room = ChatRoom.objects.create(
        course=instance,
        name=f"{instance.code} - {instance.name}" if instance.code else instance.name,
        created_by=instance.teacher,
    )
    ChatRoomMember.objects.get_or_create(room=room, user=instance.teacher)


@receiver(post_save, sender=Enrollment)
def add_student_to_chat_room(sender, instance, created, **kwargs):
    """
    Adds a newly (or re-)activated student enrollment to their course's
    chat room. Runs on every save, not just create, so re-enrolling after
    an unblock also restores chat access.
    """
    if instance.status != EnrollmentStatus.ACTIVE:
        return

    room = ChatRoom.objects.filter(course=instance.course).first()
    if room:
        ChatRoomMember.objects.get_or_create(room=room, user=instance.student)