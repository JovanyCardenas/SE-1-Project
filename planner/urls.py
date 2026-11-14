from django.urls import path
from . import views

app_name = "planner"
urlpatterns = [
    path("tasks/", views.task_list, name="task_list"),
    path("tasks/new/", views.task_edit, name="task_new"),
    path("tasks/<int:pk>/edit/", views.task_edit, name="task_edit"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task_delete"),
]
