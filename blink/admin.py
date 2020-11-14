from django.contrib import admin

from blink.models import (
    BlinkAnswer,
    BlinkAssignment,
    BlinkAssignmentQuestion,
    BlinkQuestion,
    BlinkRound,
)


@admin.register(BlinkQuestion)
class BlinkQuestionAdmin(admin.ModelAdmin):
    pass


@admin.register(BlinkRound)
class BlinkRoundAdmin(admin.ModelAdmin):
    pass


@admin.register(BlinkAnswer)
class BlinkAnswerAdmin(admin.ModelAdmin):
    pass


@admin.register(BlinkAssignment)
class BlinkAssignmentAdmin(admin.ModelAdmin):
    pass


@admin.register(BlinkAssignmentQuestion)
class BlinkAssignmentQuestionAdmin(admin.ModelAdmin):
    pass
