from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def coming_soon(request):
    return render(request, "coming_soon.html")

def home(request):
    return render(request, "pages/home.html")

def about(request):
    return render(request, "pages/about.html")

def contact(request):
    return render(request, "pages/contact.html")

def resources(request):
    return render(request, "coming_soon.html")
    # return render(request, "pages/resources.html")

@login_required
def settings(request):
    return render(request, "coming_soon.html")
    # return render(request, "pages/settings.html")

@login_required
def dashboard(request):
    return render(request, "pages/dashboard.html")