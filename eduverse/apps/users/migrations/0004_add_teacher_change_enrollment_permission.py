
from django.db import migrations


def add_permission(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    content_type, _ = ContentType.objects.get_or_create(
        app_label="courses", model="enrollment"
    )
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename="change_enrollment",
        defaults={"name": "Can change enrollment"},
    )

    teacher_group = Group.objects.get(name="Teacher")
    teacher_group.permissions.add(permission)


def remove_permission(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    try:
        teacher_group = Group.objects.get(name="Teacher")
        permission = Permission.objects.get(
            content_type__app_label="courses", codename="change_enrollment"
        )
        teacher_group.permissions.remove(permission)
    except (Group.DoesNotExist, Permission.DoesNotExist):
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_create_groups"),
    ]

    operations = [
        migrations.RunPython(add_permission, remove_permission),
    ]