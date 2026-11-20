from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import (
    LoginForm, RegisterForm, StudentProfileForm, TeacherProfileForm,
    AdminStudentCreationForm, AdminTeacherCreationForm
)
from .models import User, StudentProfile, TeacherProfile
from apps.academics.models import Department, Course, AcademicSession, TeachingAssignment, Subject
from apps.dashboard.models import log_activity
from .permissions import student_required, teacher_required, admin_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            remember_me = form.cleaned_data.get('remember_me', False)
            login(request, user)

            if not remember_me:
                request.session.set_expiry(0)  # Browser close expires session
            else:
                request.session.set_expiry(1209600)  # 2 weeks

            log_activity(user, f"Logged in from web portal", module="Authentication")
            messages.success(request, f"Welcome back, {user.display_name}!")
            return redirect('dashboard_redirect')
    else:
        form = LoginForm()

    return render(request, 'authentication/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_activity(user, f"Registered new account as {user.get_role_display()}", module="Authentication")
            login(request, user)
            messages.success(request, f"Account successfully created! Welcome to Acadify.")
            return redirect('dashboard_redirect')
    else:
        form = RegisterForm()

    return render(request, 'authentication/register.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        log_activity(request.user, "Logged out", module="Authentication")
        logout(request)
        messages.info(request, "You have been logged out securely.")
    return redirect('login')


@login_required
def dashboard_redirect(request):
    user = request.user
    if user.is_admin_user:
        return redirect('admin_dashboard')
    elif user.is_teacher_user:
        return redirect('teacher_dashboard')
    elif user.is_student_user:
        return redirect('student_dashboard')
    else:
        return redirect('admin_dashboard')


def password_reset_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        messages.success(request, "If an account exists with this email address, password reset instructions have been forwarded to the administrative desk.")
        return redirect('login')

    return render(request, 'authentication/password_reset.html')


@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            log_activity(user, "Changed password", module="Security")
            messages.success(request, "Your password was successfully updated!")
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'authentication/password_change.html', {'form': form})


@login_required
@student_required
def student_profile_view(request):
    profile = get_object_or_404(StudentProfile, user=request.user)

    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            log_activity(request.user, "Updated personal profile details", module="Student Profile")
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('student_profile')
    else:
        form = StudentProfileForm(instance=profile)

    return render(request, 'dashboards/student_profile.html', {
        'profile': profile,
        'form': form
    })


@login_required
@teacher_required
def teacher_profile_view(request):
    profile = get_object_or_404(TeacherProfile, user=request.user)

    if request.method == 'POST':
        form = TeacherProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            log_activity(request.user, "Updated faculty profile details", module="Teacher Profile")
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('teacher_profile')
    else:
        form = TeacherProfileForm(instance=profile)

    return render(request, 'dashboards/teacher_profile.html', {
        'profile': profile,
        'form': form
    })


# ==============================================================================
# ADMIN: STUDENT MANAGEMENT
# ==============================================================================
@login_required
@admin_required
def admin_students(request):
    query = request.GET.get('q', '').strip()
    dept_id = request.GET.get('department', '')
    course_id = request.GET.get('course', '')
    semester = request.GET.get('semester', '')

    students = StudentProfile.objects.select_related('user', 'department', 'course', 'batch_session').all().order_by('student_id')

    if query:
        students = students.filter(
            Q(student_id__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query)
        )
    if dept_id:
        students = students.filter(department_id=dept_id)
    if course_id:
        students = students.filter(course_id=course_id)
    if semester:
        students = students.filter(semester=semester)

    paginator = Paginator(students, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    departments = Department.objects.all()
    courses = Course.objects.all()

    return render(request, 'dashboards/admin_students.html', {
        'page_obj': page_obj,
        'departments': departments,
        'courses': courses,
        'selected_dept': dept_id,
        'selected_course': course_id,
        'selected_sem': semester,
        'query': query,
    })


@login_required
@teacher_required
def teacher_students(request):
    teacher = getattr(request.user, 'teacher_profile', None)
    query = request.GET.get('q', '').strip()

    if teacher:
        assigned_subjects = Subject.objects.filter(teaching_assignments__teacher=teacher)
        students = StudentProfile.objects.filter(
            course__in=assigned_subjects.values_list('course', flat=True),
            semester__in=assigned_subjects.values_list('semester', flat=True),
            user__is_active=True
        ).distinct().select_related('user', 'department', 'course').order_by('student_id')
    else:
        students = StudentProfile.objects.none()

    if query:
        students = students.filter(
            Q(student_id__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )

    paginator = Paginator(students, 15)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'dashboards/admin_students.html', {
        'page_obj': page_obj,
        'query': query,
    })


@login_required
@admin_required
def admin_student_add(request):
    if request.method == 'POST':
        form = AdminStudentCreationForm(request.POST)
        if form.is_valid():
            # Create user
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data.get('last_name', ''),
                phone=form.cleaned_data.get('phone', ''),
                role=User.ROLE_STUDENT
            )
            # Create profile
            profile = form.save(commit=False)
            profile.user = user
            profile.save()

            log_activity(request.user, f"Added student {profile.student_id} ({user.display_name})", module="Student Management")
            messages.success(request, f"Student {user.display_name} ({profile.student_id}) created successfully.")
            return redirect('admin_students')
        else:
            messages.error(request, "Failed to create student. Please correct the highlighted errors.")
    else:
        form = AdminStudentCreationForm()

    return render(request, 'dashboards/admin_student_form.html', {'form': form, 'title': 'Add New Student'})


@login_required
@admin_required
def admin_student_edit(request, pk):
    profile = get_object_or_404(StudentProfile, pk=pk)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            # Also allow department and course update from admin
            dept_id = request.POST.get('department')
            course_id = request.POST.get('course')
            sem = request.POST.get('semester')
            if dept_id:
                profile.department_id = dept_id
            if course_id:
                profile.course_id = course_id
            if sem:
                profile.semester = sem
            profile.save()

            log_activity(request.user, f"Updated student {profile.student_id}", module="Student Management")
            messages.success(request, f"Student {profile.user.display_name} updated successfully.")
            return redirect('admin_students')
    else:
        form = StudentProfileForm(instance=profile)

    departments = Department.objects.all()
    courses = Course.objects.all()
    return render(request, 'dashboards/admin_student_form.html', {
        'form': form,
        'profile': profile,
        'departments': departments,
        'courses': courses,
        'title': f"Edit Student - {profile.student_id}"
    })


@login_required
@admin_required
def admin_student_toggle_status(request, pk):
    profile = get_object_or_404(StudentProfile, pk=pk)
    user = profile.user
    user.is_active = not user.is_active
    user.save()
    status_str = "activated" if user.is_active else "deactivated"
    log_activity(request.user, f"{status_str.capitalize()} student {profile.student_id}", module="Student Management")
    messages.info(request, f"Student {user.display_name} account has been {status_str}.")
    return redirect('admin_students')


@login_required
@admin_required
def admin_student_detail(request, pk):
    profile = get_object_or_404(StudentProfile.objects.select_related('user', 'department', 'course', 'batch_session'), pk=pk)
    attendance_records = profile.attendance_records.select_related('subject').order_by('-date')[:10]
    total_att = profile.attendance_records.count()
    present_att = profile.attendance_records.filter(status='PRESENT').count()
    att_pct = round((present_att / total_att * 100), 1) if total_att > 0 else 0

    results = profile.results.select_related('examination', 'subject').order_by('-created_at')[:10]
    fees = profile.fee_records.order_by('-due_date')[:10]

    return render(request, 'dashboards/admin_student_detail.html', {
        'profile': profile,
        'attendance_records': attendance_records,
        'total_att': total_att,
        'att_pct': att_pct,
        'results': results,
        'fees': fees,
    })


# ==============================================================================
# ADMIN: TEACHER MANAGEMENT
# ==============================================================================
@login_required
@admin_required
def admin_teachers(request):
    query = request.GET.get('q', '').strip()
    dept_id = request.GET.get('department', '')

    teachers = TeacherProfile.objects.select_related('user', 'department').all()

    if query:
        teachers = teachers.filter(
            Q(employee_id__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query)
        )
    if dept_id:
        teachers = teachers.filter(department_id=dept_id)

    paginator = Paginator(teachers, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    departments = Department.objects.all()

    return render(request, 'dashboards/admin_teachers.html', {
        'page_obj': page_obj,
        'departments': departments,
        'selected_dept': dept_id,
        'query': query,
    })


@login_required
@admin_required
def admin_teacher_add(request):
    if request.method == 'POST':
        form = AdminTeacherCreationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data.get('last_name', ''),
                phone=form.cleaned_data.get('phone', ''),
                role=User.ROLE_TEACHER
            )
            profile = form.save(commit=False)
            profile.user = user
            profile.save()

            log_activity(request.user, f"Added teacher {profile.employee_id} ({user.display_name})", module="Teacher Management")
            messages.success(request, f"Teacher {user.display_name} ({profile.employee_id}) created successfully.")
            return redirect('admin_teachers')
        else:
            messages.error(request, "Failed to create teacher. Please check errors.")
    else:
        form = AdminTeacherCreationForm()

    return render(request, 'dashboards/admin_teacher_form.html', {'form': form, 'title': 'Add New Teacher'})


@login_required
@admin_required
def admin_teacher_edit(request, pk):
    profile = get_object_or_404(TeacherProfile, pk=pk)
    if request.method == 'POST':
        form = TeacherProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            dept_id = request.POST.get('department')
            if dept_id:
                profile.department_id = dept_id
                profile.save()

            log_activity(request.user, f"Updated teacher {profile.employee_id}", module="Teacher Management")
            messages.success(request, f"Teacher {profile.user.display_name} updated successfully.")
            return redirect('admin_teachers')
    else:
        form = TeacherProfileForm(instance=profile)

    departments = Department.objects.all()
    return render(request, 'dashboards/admin_teacher_form.html', {
        'form': form,
        'profile': profile,
        'departments': departments,
        'title': f"Edit Teacher - {profile.employee_id}"
    })


@login_required
@admin_required
def admin_teacher_toggle_status(request, pk):
    profile = get_object_or_404(TeacherProfile, pk=pk)
    user = profile.user
    user.is_active = not user.is_active
    user.save()
    status_str = "activated" if user.is_active else "deactivated"
    log_activity(request.user, f"{status_str.capitalize()} teacher {profile.employee_id}", module="Teacher Management")
    messages.info(request, f"Teacher {user.display_name} account has been {status_str}.")
    return redirect('admin_teachers')
