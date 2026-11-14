from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from .forms import PersonalTaskForm
from .models import PersonalTask


@login_required
def task_list(request):
    return render(request, "planner/personal_list.html", {"tasks": PersonalTask.objects.filter(owner=request.user).select_related("course")})


@login_required
@require_http_methods(["GET", "POST"])
def task_edit(request, pk=None):
    task = get_object_or_404(PersonalTask, pk=pk, owner=request.user) if pk else PersonalTask(owner=request.user)
    form = PersonalTaskForm(request.POST if request.method == "POST" else None, instance=task, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("planner:task_list")
    return render(request, "planner/personal_form.html", {"form": form, "task": task})


@login_required
@require_http_methods(["GET", "POST"])
def task_delete(request, pk):
    task = get_object_or_404(PersonalTask, pk=pk, owner=request.user)
    if request.method == "POST":
        task.delete()
        return redirect("planner:task_list")
    return render(request, "planner/personal_delete.html", {"task": task})
