from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Department, Course, Subject, AcademicSession, Enrollment, TeachingAssignment
from .forms import (
    DepartmentForm, CourseForm, SubjectForm, AcademicSessionForm,
    EnrollmentForm, TeachingAssignmentForm
)
from apps.accounts.permissions import admin_required
from apps.dashboard.models import log_activity


@login_required
@admin_required
def admin_departments(request):
    query = request.GET.get('q', '').strip()
    departments = Department.objects.annotate(
        total_courses=Count('courses', distinct=True),
        total_students=Count('students', distinct=True)
    ).order_by('name')

    if query:
        departments = departments.filter(Q(name__icontains=query) | Q(code__icontains=query))

    form = DepartmentForm()
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            log_activity(request.user, f"Created department {dept.name} ({dept.code})", module="Academics")
            messages.success(request, f"Department '{dept.name}' created successfully.")
            return redirect('admin_departments')
        else:
            messages.error(request, "Failed to create department. Please check the inputs.")

    paginator = Paginator(departments, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'academics/departments.html', {
        'page_obj': page_obj,
        'form': form,
        'query': query,
    })


@login_required
@admin_required
def admin_department_edit(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            log_activity(request.user, f"Updated department {dept.code}", module="Academics")
            messages.success(request, f"Department '{dept.name}' updated successfully.")
            return redirect('admin_departments')
    else:
        form = DepartmentForm(instance=dept)

    return render(request, 'academics/department_edit.html', {'dept': dept, 'form': form})


@login_required
@admin_required
def admin_department_delete(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        name = dept.name
        dept.delete()
        log_activity(request.user, f"Deleted department {name}", module="Academics")
        messages.success(request, f"Department '{name}' has been deleted.")
    return redirect('admin_departments')


@login_required
@admin_required
def admin_courses(request):
    query = request.GET.get('q', '').strip()
    dept_id = request.GET.get('department', '')

    courses = Course.objects.select_related('department').annotate(
        total_subjects=Count('subjects', distinct=True),
        total_students=Count('students', distinct=True)
    ).order_by('name')

    if query:
        courses = courses.filter(Q(name__icontains=query) | Q(code__icontains=query))
    if dept_id:
        courses = courses.filter(department_id=dept_id)

    form = CourseForm()
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            c = form.save()
            log_activity(request.user, f"Created course {c.code}", module="Academics")
            messages.success(request, f"Course '{c.name}' added successfully.")
            return redirect('admin_courses')
        else:
            messages.error(request, "Failed to create course. Please review the errors.")

    departments = Department.objects.all()
    paginator = Paginator(courses, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'academics/courses.html', {
        'page_obj': page_obj,
        'form': form,
        'departments': departments,
        'selected_dept': dept_id,
        'query': query,
    })


@login_required
@admin_required
def admin_course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            log_activity(request.user, f"Updated course {course.code}", module="Academics")
            messages.success(request, f"Course '{course.name}' updated successfully.")
            return redirect('admin_courses')
    else:
        form = CourseForm(instance=course)

    return render(request, 'academics/course_edit.html', {'course': course, 'form': form})


@login_required
@admin_required
def admin_course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        name = course.name
        course.delete()
        log_activity(request.user, f"Deleted course {name}", module="Academics")
        messages.success(request, f"Course '{name}' has been deleted.")
    return redirect('admin_courses')


@login_required
@admin_required
def admin_subjects(request):
    query = request.GET.get('q', '').strip()
    course_id = request.GET.get('course', '')
    sem = request.GET.get('semester', '')

    subjects = Subject.objects.select_related('course')

    if query:
        subjects = subjects.filter(Q(name__icontains=query) | Q(code__icontains=query))
    if course_id:
        subjects = subjects.filter(course_id=course_id)
    if sem:
        subjects = subjects.filter(semester=sem)

    form = SubjectForm()
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            s = form.save()
            log_activity(request.user, f"Added subject {s.code}", module="Academics")
            messages.success(request, f"Subject '{s.name}' added successfully.")
            return redirect('admin_subjects')
        else:
            messages.error(request, "Failed to create subject. Please check inputs.")

    courses = Course.objects.all()
    paginator = Paginator(subjects, 15)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'academics/subjects.html', {
        'page_obj': page_obj,
        'form': form,
        'courses': courses,
        'selected_course': course_id,
        'selected_sem': sem,
        'query': query,
    })


@login_required
@admin_required
def admin_subject_edit(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            log_activity(request.user, f"Updated subject {subject.code}", module="Academics")
            messages.success(request, f"Subject '{subject.name}' updated successfully.")
            return redirect('admin_subjects')
    else:
        form = SubjectForm(instance=subject)

    return render(request, 'academics/subject_edit.html', {'subject': subject, 'form': form})


@login_required
@admin_required
def admin_subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        name = subject.name
        subject.delete()
        log_activity(request.user, f"Deleted subject {name}", module="Academics")
        messages.success(request, f"Subject '{name}' has been deleted.")
    return redirect('admin_subjects')


@login_required
@admin_required
def admin_enrollments(request):
    query = request.GET.get('q', '').strip()
    session_id = request.GET.get('session', '')
    course_id = request.GET.get('course', '')

    enrollments = Enrollment.objects.select_related('student__user', 'course', 'session')

    if query:
        enrollments = enrollments.filter(
            Q(student__student_id__icontains=query) |
            Q(student__user__first_name__icontains=query) |
            Q(student__user__last_name__icontains=query)
        )
    if session_id:
        enrollments = enrollments.filter(session_id=session_id)
    if course_id:
        enrollments = enrollments.filter(course_id=course_id)

    form = EnrollmentForm()
    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            enr = form.save()
            # Also update student's primary course & semester
            enr.student.course = enr.course
            enr.student.semester = enr.semester
            enr.student.batch_session = enr.session
            enr.student.save()

            log_activity(request.user, f"Enrolled student {enr.student.student_id} into {enr.course.code}", module="Enrollments")
            messages.success(request, f"Student {enr.student.student_id} successfully enrolled.")
            return redirect('admin_enrollments')
        else:
            messages.error(request, "Enrollment error. Verify if the student is already enrolled for this semester.")

    sessions = AcademicSession.objects.all()
    courses = Course.objects.all()
    paginator = Paginator(enrollments, 15)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'academics/enrollments.html', {
        'page_obj': page_obj,
        'form': form,
        'sessions': sessions,
        'courses': courses,
        'selected_session': session_id,
        'selected_course': course_id,
        'query': query,
    })


@login_required
@admin_required
def admin_enrollment_delete(request, pk):
    enr = get_object_or_404(Enrollment, pk=pk)
    if request.method == 'POST':
        sid = enr.student.student_id
        enr.delete()
        log_activity(request.user, f"Removed enrollment for {sid}", module="Enrollments")
        messages.success(request, f"Enrollment for {sid} removed.")
    return redirect('admin_enrollments')
