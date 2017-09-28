from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.urls import reverse


###############################"""

def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(reverse('index'))
        else:
            return redirect(reverse('login'))
    return render(request, template_name="account/login.html")




def logout_user(request):
    logout(request)
    return redirect(reverse('login'))