from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .forms import SignupForm, LoginForm
from django.contrib.auth.decorators import login_required

def signup_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Check if email is already taken
        if User.objects.filter(email=email).exists():
            messages.error(request, "Helios: Email is already registered.")
            return render(request, "account/signup.html")

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, "Helios: Passwords do not match.")
            return render(request, "account/signup.html")

        # Validate password
        try:
            validate_password(password)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, f"Helios: {error}")
            return render(request, "account/signup.html")

        # Create user
        user = User.objects.create_user(username=email, email=email, password=password)
        messages.success(request, "Helios: Account created successfully! Please begin your journey.")
        return redirect("login")  # Adjust to your actual login view

    return render(request, "account/signup.html")

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Authenticate user
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Helios: Logged in successfully!")
            return redirect('home') 
        else:
            messages.error(request, "Helios: Invalid email or password.")

    return render(request, 'account/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Helios: Logged out successfully!')
    return redirect('home')  # Adjust to your actual login view
