from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, UserRole


@receiver(post_save, sender=User)
def assign_role_group(sender, instance, created, **kwargs):
    """
    Adds a newly created user to the Group matching their role.
    Only fires on creation — changing role afterwards does not
    move the user between groups (see note below).
    """
    if not created:
        return

    group_name = "Student" if instance.role == UserRole.STUDENT else "Teacher"

    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        # Groups migration hasn't run yet, or was renamed/deleted.
        return

    instance.groups.add(group)