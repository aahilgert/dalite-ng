
"""
from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

from .group import StudentGroup
from .student import StudentGroupMembership

from course_flow.views import add_student_to_group, remove_student_from_group


class StudentGroupCourse(models.Model):
    student_group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE)
    course = models.ForeignKey("course_flow.Course", on_delete=models.CASCADE)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Group-Course Link"
        verbose_name_plural = "Group-Course Links"


@receiver(pre_save, sender=StudentGroupMembership)
def add_to_course_flow(sender, instance, **kwargs):
    if StudentGroupCourse.objects.filter(student_group=instance.group).first():
        add_student_to_group(
            group.student.student,
            StudentGroupCourse.objects.get(
                student_group=instance.group
            ).course,
        )


@receiver(pre_delete, sender=StudentGroupMembership)
def add_to_course_flow(sender, instance, **kwargs):
    if StudentGroupCourse.objects.filter(student_group=instance.group).first():
        remove_student_from_group(
            group.student.student,
            StudentGroupCourse.objects.get(
                student_group=instance.group
            ).course,
        )
"""
