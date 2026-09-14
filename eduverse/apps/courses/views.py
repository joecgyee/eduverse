from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.feed.models import Notification, NotificationType

from .forms import *
from .models import *

from django.core.paginator import Paginator
from django.db.models import Q


# ---------------------------------------------------------------------------
# Browsing
# ---------------------------------------------------------------------------

@login_required
def course_list_view(request):
    """
    Teachers see 'My Courses' (their own, any status) plus 'Available Courses'
    from everyone else.
    Students see 'My Courses' (courses they're actively enrolled in) plus
    'Available Courses' (all published courses).
    Both sections support search by course name, code, or teacher name.
    """
    query = request.GET.get("q", "").strip()

    def apply_search(qs):
        if not query:
            return qs
        return qs.filter(
            Q(name__icontains=query)
            | Q(code__icontains=query)
            | Q(teacher__first_name__icontains=query)
            | Q(teacher__last_name__icontains=query)
        ).distinct()

    base_qs = Course.objects.select_related("teacher", "teacher__teacher_profile")

    my_courses_page = None

    if request.user.is_teacher:
        my_courses_qs = apply_search(base_qs.filter(teacher=request.user))
        my_paginator = Paginator(my_courses_qs, 6)
        my_courses_page = my_paginator.get_page(request.GET.get("mine_page"))

        # Exclude the teacher's own courses from "Available Courses" to avoid duplicates.
        published_qs = apply_search(
            base_qs.filter(status=CourseStatus.PUBLISHED).exclude(teacher=request.user)
        )
    else:
        enrolled_course_ids = Enrollment.objects.filter(
            student=request.user, status=EnrollmentStatus.ACTIVE
        ).values_list("course_id", flat=True)

        my_courses_qs = apply_search(base_qs.filter(id__in=enrolled_course_ids))
        my_paginator = Paginator(my_courses_qs, 6)
        my_courses_page = my_paginator.get_page(request.GET.get("mine_page"))

        # Exclude courses the student is already enrolled in from "Available Courses".
        published_qs = apply_search(
            base_qs.filter(status=CourseStatus.PUBLISHED).exclude(id__in=enrolled_course_ids)
        )

    published_paginator = Paginator(published_qs, 6)
    published_page = published_paginator.get_page(request.GET.get("page"))

    return render(request, "courses/course_list.html", {
        "my_courses_page": my_courses_page,
        "published_page": published_page,
        "query": query,
    })


@login_required
def course_detail_view(request, pk):
    course = get_object_or_404(Course, pk=pk)

    is_enrolled = False
    if request.user.is_student:
        is_enrolled = Enrollment.objects.filter(
            student=request.user, course=course, status=EnrollmentStatus.ACTIVE
        ).exists()

    context = {
        "course": course,
        "is_enrolled": is_enrolled,
        "is_owner": request.user.is_teacher and course.teacher_id == request.user.id,
        "materials": course.materials.prefetch_related("attachments") if is_enrolled or request.user.is_teacher else None,
        "feedback": course.feedback.select_related("student"),
        "chat_room": course.chat_rooms.first(),
    }
    return render(request, "courses/course_detail.html", context)


# ---------------------------------------------------------------------------
# Teacher: course management
# ---------------------------------------------------------------------------

@login_required
@permission_required("courses.add_course", raise_exception=True)
def course_create_view(request):
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            messages.success(request, "Course created.")
            return redirect("courses:detail", pk=course.pk)
    else:
        form = CourseForm()

    return render(request, "courses/course_form.html", {"form": form})


@login_required
@permission_required("courses.change_course", raise_exception=True)
def course_update_view(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if course.teacher_id != request.user.id:
        raise PermissionDenied("You can only edit your own courses.")

    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated.")
            return redirect("courses:detail", pk=course.pk)
    else:
        form = CourseForm(instance=course)

    return render(request, "courses/course_form.html", {"form": form, "course": course})


@login_required
@permission_required("courses.view_enrollment", raise_exception=True)
def course_students_view(request, pk):
    """Teacher's view of students enrolled in their course."""
    course = get_object_or_404(Course, pk=pk)
    if course.teacher_id != request.user.id:
        raise PermissionDenied("You can only view students on your own courses.")

    enrollments = course.enrollments.select_related("student").order_by("student__last_name")
    return render(request, "courses/course_students.html", {"course": course, "enrollments": enrollments})


@login_required
@permission_required("courses.change_enrollment", raise_exception=True)
def block_student_view(request, pk, enrollment_id):
    """Teacher blocks/removes a student from their course."""
    course = get_object_or_404(Course, pk=pk)
    if course.teacher_id != request.user.id:
        raise PermissionDenied("You can only manage enrollments on your own courses.")

    enrollment = get_object_or_404(Enrollment, pk=enrollment_id, course=course)

    if request.method == "POST":
        enrollment.status = EnrollmentStatus.BLOCKED
        enrollment.save(update_fields=["status"])
        messages.info(request, f"{enrollment.student.get_full_name()} has been blocked from this course.")

    return redirect("courses:students", pk=course.pk)


# ---------------------------------------------------------------------------
# Teacher: course materials
# ---------------------------------------------------------------------------

@login_required
@permission_required("courses.add_coursematerial", raise_exception=True)
def course_material_create_view(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if course.teacher_id != request.user.id:
        raise PermissionDenied("You can only add materials to your own courses.")

    if request.method == "POST":
        form = CourseMaterialForm(request.POST)
        formset = CourseMaterialAttachmentFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            material = form.save(commit=False)
            material.course = course
            material.uploaded_by = request.user
            material.save()

            formset.instance = material
            formset.save()

            # Notify enrolled students of new material.
            active_enrollments = course.enrollments.filter(status=EnrollmentStatus.ACTIVE)
            Notification.objects.bulk_create([
                Notification(
                    recipient=e.student,
                    type=NotificationType.COURSE_MATERIAL,
                    message=f"New material posted in {course.code} - {course.name}: {material.title}",
                    course=course,
                )
                for e in active_enrollments
            ])

            messages.success(request, "Material uploaded.")
            return redirect("courses:detail", pk=course.pk)
    else:
        form = CourseMaterialForm()
        formset = CourseMaterialAttachmentFormSet()

    return render(
        request, "courses/course_material_form.html",
        {"form": form, "formset": formset, "course": course},
    )


@login_required
@permission_required("courses.change_coursematerial", raise_exception=True)
def course_material_update_view(request, pk, material_id):
    course = get_object_or_404(Course, pk=pk)
    material = get_object_or_404(CourseMaterial, pk=material_id, course=course)

    if course.teacher_id != request.user.id:
        raise PermissionDenied("You can only edit materials on your own courses.")

    if request.method == "POST":
        form = CourseMaterialForm(request.POST, instance=material)
        formset = CourseMaterialAttachmentFormSet(request.POST, request.FILES, instance=material)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Material updated.")
            return redirect("courses:detail", pk=course.pk)
    else:
        form = CourseMaterialForm(instance=material)
        formset = CourseMaterialAttachmentFormSet(instance=material)

    return render(
        request, "courses/course_material_form.html",
        {"form": form, "formset": formset, "course": course, "material": material},
    )


@login_required
@permission_required("courses.delete_coursematerial", raise_exception=True)
def course_material_delete_view(request, pk, material_id):
    course = get_object_or_404(Course, pk=pk)
    material = get_object_or_404(CourseMaterial, pk=material_id, course=course)

    if course.teacher_id != request.user.id:
        raise PermissionDenied("You can only delete materials on your own courses.")

    if request.method == "POST":
        material.delete()
        messages.info(request, "Material deleted.")

    return redirect("courses:detail", pk=course.pk)


# ---------------------------------------------------------------------------
# Student: enrolment
# ---------------------------------------------------------------------------

@login_required
@permission_required("courses.add_enrollment", raise_exception=True)
def enrol_view(request, pk):
    course = get_object_or_404(Course, pk=pk, status=CourseStatus.PUBLISHED)

    if not request.user.is_student:
        raise PermissionDenied("Only students can enrol in courses.")

    existing = Enrollment.objects.filter(student=request.user, course=course).first()
    if existing and existing.status == EnrollmentStatus.BLOCKED:
        messages.error(request, "You have been blocked from this course and cannot re-enrol.")
        return redirect("courses:detail", pk=course.pk)

    if request.method == "POST":
        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user, course=course,
            defaults={"status": EnrollmentStatus.ACTIVE},
        )
        if created:
            # Notify the teacher of the new enrollment.
            Notification.objects.create(
                recipient=course.teacher,
                type=NotificationType.ENROLLMENT,
                message=f"{request.user.get_full_name()} enrolled in {course.code} - {course.name}.",
                course=course,
            )
            messages.success(request, f"You are now enrolled in {course.name}.")
        else:
            messages.info(request, "You are already enrolled in this course.")

    return redirect("courses:detail", pk=course.pk)


@login_required
def course_classmates_view(request, pk):
    """Lets an enrolled student browse other students enrolled in the same course."""
    course = get_object_or_404(Course, pk=pk)

    is_enrolled = Enrollment.objects.filter(
        student=request.user, course=course, status=EnrollmentStatus.ACTIVE
    ).exists()
    if not is_enrolled:
        raise PermissionDenied("Only students enrolled in this course can view classmates.")

    classmates = Enrollment.objects.filter(
        course=course, status=EnrollmentStatus.ACTIVE
    ).exclude(student=request.user).select_related("student").order_by("student__first_name")

    return render(request, "courses/course_classmates.html", {"course": course, "classmates": classmates})


# ---------------------------------------------------------------------------
# Student: feedback
# ---------------------------------------------------------------------------

@login_required
@permission_required("courses.add_coursefeedback", raise_exception=True)
def course_feedback_create_view(request, pk):
    course = get_object_or_404(Course, pk=pk)

    is_enrolled = Enrollment.objects.filter(
        student=request.user, course=course, status=EnrollmentStatus.ACTIVE
    ).exists()
    if not is_enrolled:
        raise PermissionDenied("Only enrolled students can leave feedback for this course.")

    existing = CourseFeedback.objects.filter(course=course, student=request.user).first()

    if request.method == "POST":
        form = CourseFeedbackForm(request.POST, instance=existing)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.course = course
            feedback.student = request.user
            feedback.save()
            messages.success(request, "Thanks for your feedback.")
            return redirect("courses:detail", pk=course.pk)
    else:
        form = CourseFeedbackForm(instance=existing)

    return render(request, "courses/course_feedback_form.html", {"form": form, "course": course})