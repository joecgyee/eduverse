from django.db import migrations

# (app_label, model_name, verbose_name) — verbose_name must match what
# Django auto-derives from the model class name, since we build
# permission `name` strings from it (e.g. "Can view chat message").
MODEL_SPECS = [
    ("auth", "group", "group"),
    ("auth", "permission", "permission"),
    ("contenttypes", "contenttype", "content type"),
    ("chat", "chatmessage", "chat message"),
    ("chat", "chatroom", "chat room"),
    ("chat", "chatroommember", "chat room member"),
    ("courses", "course", "course"),
    ("courses", "coursefeedback", "course feedback"),
    ("courses", "coursematerial", "course material"),
    ("courses", "coursematerialattachment", "course material attachment"),
    ("courses", "enrollment", "enrollment"),
    ("feed", "feed", "feed"),
    ("feed", "feedcomment", "feed comment"),
    ("feed", "notification", "notification"),
    ("users", "studentprofile", "student profile"),
    ("users", "teacherprofile", "teacher profile"),
    ("users", "user", "user"),
]

GROUP_PERMISSIONS = {
    "Teacher": {
        ("auth", "group"): {"view"},
        ("auth", "permission"): {"view"},
        ("chat", "chatmessage"): {"add", "change", "delete", "view"},
        ("chat", "chatroom"): {"add", "change", "delete", "view"},
        ("chat", "chatroommember"): {"add", "change", "delete", "view"},
        ("contenttypes", "contenttype"): {"view"},
        ("courses", "course"): {"add", "change", "delete", "view"},
        ("courses", "coursefeedback"): {"view"},
        ("courses", "coursematerial"): {"add", "change", "delete", "view"},
        ("courses", "coursematerialattachment"): {"add", "change", "delete", "view"},
        ("courses", "enrollment"): {"view"},
        ("feed", "feed"): {"add", "change", "delete", "view"},
        ("feed", "feedcomment"): {"add", "change", "delete", "view"},
        ("feed", "notification"): {"view"},
        ("users", "studentprofile"): {"view"},
        ("users", "teacherprofile"): {"add", "change", "delete", "view"},
        ("users", "user"): {"view"},
    },
    "Student": {
        ("auth", "group"): {"view"},
        ("chat", "chatmessage"): {"add", "change", "delete", "view"},
        ("chat", "chatroom"): {"add", "change", "delete", "view"},
        ("chat", "chatroommember"): {"add", "change", "delete", "view"},
        ("contenttypes", "contenttype"): {"view"},
        ("courses", "course"): {"view"},
        ("courses", "coursefeedback"): {"add", "change", "delete", "view"},
        ("courses", "coursematerial"): {"view"},
        ("courses", "coursematerialattachment"): {"view"},
        ("courses", "enrollment"): {"add", "change", "delete", "view"},
        ("feed", "feed"): {"add", "change", "delete", "view"},
        ("feed", "feedcomment"): {"add", "change", "delete", "view"},
        ("feed", "notification"): {"view"},
        ("users", "studentprofile"): {"add", "change", "delete", "view"},
        ("users", "teacherprofile"): {"view"},
        ("users", "user"): {"view"},
    },
}


def _get_or_create_permission(Permission, ContentType, app_label, model_name, verbose_name, action):
    content_type, _ = ContentType.objects.get_or_create(
        app_label=app_label, model=model_name
    )
    codename = f"{action}_{model_name}"
    name = f"Can {action} {verbose_name}"
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type, codename=codename, defaults={"name": name}
    )
    return permission


def create_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    verbose_lookup = {
        (app_label, model_name): verbose_name
        for app_label, model_name, verbose_name in MODEL_SPECS
    }

    for group_name, model_actions in GROUP_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        permissions = []
        for (app_label, model_name), actions in model_actions.items():
            verbose_name = verbose_lookup[(app_label, model_name)]
            for action in actions:
                permissions.append(
                    _get_or_create_permission(
                        Permission, ContentType, app_label, model_name, verbose_name, action
                    )
                )
        group.permissions.set(permissions)


def delete_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=["Teacher", "Student"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_alter_user_photo"),
        ("chat", "0001_initial"),
        ("courses", "0001_initial"),
        ("feed", "0002_rename_comment_feedcomment"),
    ]

    operations = [
        migrations.RunPython(create_groups, delete_groups),
    ]