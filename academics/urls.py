from django.urls import path

from . import views

app_name = "academics"
urlpatterns = [
    path("courses/add/", views.course_add, name="course_add"),
    path("courses/<int:pk>/", views.course_detail, name="course_detail"),
    path("syllabus/<uuid:pk>/review/", views.syllabus_review, name="syllabus_review"),
]
