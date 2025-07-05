from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, LoginForm
from .models import Note  # ✅ Import the Note model
import random

# -------------------- Standard Auth Views --------------------

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # Hash password
            user.save()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('notes_list')  # ✅ Redirect to notes after login
        else:
            error = "Invalid username or password"
    return render(request, 'login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')

# -------------------- Home View --------------------

@login_required
def home_view(request):
    return render(request, 'home.html')


# -------------------- Notes Views --------------------

@login_required
def notes_list(request):
    """View all notes for the logged-in user."""
    notes = Note.objects.filter(owner=request.user)
    return render(request, 'notes_list.html', {'notes': notes})


@login_required
def add_note(request):
    """Add a new note."""
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        Note.objects.create(
            title=title,
            content=content,
            owner=request.user
        )
        return redirect('notes_list')
    return render(request, 'add_note.html')


@login_required
def edit_note(request, note_id):
    """Edit an existing note."""
    note = get_object_or_404(Note, id=note_id, owner=request.user)
    if request.method == 'POST':
        note.title = request.POST.get('title')
        note.content = request.POST.get('content')
        note.save()
        return redirect('notes_list')
    return render(request, 'edit_note.html', {'note': note})


@login_required
def delete_note(request, note_id):
    """Delete a note."""
    note = get_object_or_404(Note, id=note_id, owner=request.user)
    if request.method == 'POST':
        note.delete()
        return redirect('notes_list')
    return render(request, 'delete_note.html', {'note': note})


# -------------------- OTP Password Reset --------------------

# Simple in-memory OTP storage (for demo)
otp_storage = {}

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            otp = str(random.randint(100000, 999999))
            otp_storage[email] = otp
            send_mail(
                subject='Your OTP Code',
                message=f'Your OTP is: {otp}',
                from_email='admin@example.com',  # Replace with your sender email
                recipient_list=[email],
                fail_silently=False,
            )
            request.session['reset_email'] = email
            return redirect('verify_otp')
        else:
            return render(request, 'forgot_password.html', {'error': 'Email not registered'})
    return render(request, 'forgot_password.html')


def verify_otp_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')  # No email in session
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        if otp_storage.get(email) == user_otp:
            del otp_storage[email]  # Clean up OTP immediately
            return redirect('reset_password')
        else:
            return render(request, 'verify_otp.html', {'error': 'Invalid OTP'})
    return render(request, 'verify_otp.html')


def reset_password_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')  # Prevent access without email
    if request.method == 'POST':
        new_password = request.POST.get('password')
        user = User.objects.filter(email=email).first()
        if user:
            user.set_password(new_password)
            user.save()
            request.session.pop('reset_email', None)
            return redirect('login')
        else:
            return render(request, 'reset_password.html', {'error': 'User not found.'})
    return render(request, 'reset_password.html')


# -------------------- Test Email --------------------

def send_test_email_view(request):
    send_mail(
        subject='Test Email from Django (SMTP)',
        message='Hello! This is a test email sent from Django using Gmail SMTP.',
        from_email='admin@example.com',  # Replace with your sender email
        recipient_list=['janani05pancha@gmail.com'],
        fail_silently=False,
    )
    return HttpResponse("✅ Test email sent successfully!")
