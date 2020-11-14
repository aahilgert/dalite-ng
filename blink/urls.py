from django.urls import path
from django.views.decorators.cache import cache_page

from blink import views


app_name = "blink"

urlpatterns = [
    path(
        "<int:pk>/",
        views.BlinkQuestionFormView.as_view(),
        name="blink-question",
    ),
    path(
        "<int:pk>/summary/",
        views.BlinkQuestionDetailView.as_view(),
        name="blink-summary",
    ),
    path("<int:pk>/count/", views.blink_count, name="blink-count",),
    path("<int:pk>/close/", views.blink_close, name="blink-close",),
    path(
        "<int:pk>/latest_results/",
        views.blink_latest_results,
        name="blink-results",
    ),
    path("<int:pk>/reset/", views.blink_reset, name="blink-reset",),
    path("<int:pk>/status/", views.blink_status, name="blink-status",),
    path("<username>/", views.blink_get_current, name="blink-get-current",),
    path(
        "<username>/url/",
        cache_page(1)(views.blink_get_current_url),
        name="blink-get-current-url",
    ),
    path("<int:pk>/get_next/", views.blink_get_next, name="blink-get-next",),
    path("waiting/<username>/", views.blink_waiting, name="blink-waiting",),
    path(
        "waiting/<username>/<int:assignment>/",
        views.blink_waiting,
        name="blink-waiting",
    ),
    path(
        "assignment/create/",
        views.BlinkAssignmentCreate.as_view(),
        name="blinkAssignment-create",
    ),
    path(
        "assignment/<int:pk>/delete/",
        views.blink_assignment_delete,
        name="blinkAssignment-delete",
    ),
    path(
        "assignment/<int:pk>/set_time/",
        views.blink_assignment_set_time,
        name="blinkAssignment-set-time",
    ),
    path(
        "assignment/<int:pk>/start/",
        views.blink_assignment_start,
        name="blinkAssignment-start",
    ),
    path(
        "assignment/<int:pk>/update/",
        views.BlinkAssignmentUpdate.as_view(),
        name="blinkAssignment-update",
    ),
]
