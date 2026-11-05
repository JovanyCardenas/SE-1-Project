from django.urls import path
from . import views
urlpatterns = [
 path('courses/', views.courses, name='courses'),
 path('courses/new/', views.course_form, name='course_new'),
 path('courses/<int:pk>/', views.course_detail, name='course_detail'),
 path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),
 path('courses/<int:pk>/edit/', views.course_form, name='course_edit'),
 path('courses/<int:pk>/upload/', views.syllabus_upload, name='syllabus_upload'),
 path('courses/<int:pk>/review/', views.syllabus_review, name='syllabus_review'),
 path('tasks/', views.tasks, name='tasks'),
 path('tasks/new/', views.task_form, name='task_new'),
 path('tasks/<int:pk>/edit/', views.task_form, name='task_edit'),
 path('tasks/<int:pk>/toggle/', views.task_toggle, name='task_toggle'),
 path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
 path('calendar/', views.calendar_view, name='calendar'),
]
