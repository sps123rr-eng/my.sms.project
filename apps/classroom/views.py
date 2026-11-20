from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Sum
from .models import Timetable, Assignment, Submission, StudyMaterial, Examination, Result
from .forms import (
    TimetableForm, AssignmentForm, SubmissionForm, SubmissionGradingForm,
    StudyMaterialForm, ExaminationForm, ResultForm
)
from apps.academics.models import Subject, Course, AcademicSession
from apps.accounts.models import StudentProfile, TeacherProfile
from apps.accounts.permissions import admin_required, teacher_required, student_required
from apps.dashboard.models import log_activity


# ==============================================================================
# TIMETABLE MODULE (SCREEN 8)
# ==============================================================================
@login_required
def timetable_view(request):
    days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
    day_labels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    # Standard academic time slots
    slots = [
        ('09:00:00', '10:00:00', '09:00 - 10:00'),
        ('10:30:00', '11:30:00', '10:30 - 11:30'),
        ('12:00:00', '13:00:00', '12:00 - 01:00'),
        ('14:00:00', '15:00:00', '02:00 - 03:00'),
        ('15:30:00', '16:30:00', '03:30 - 04:30'),
    ]

    form = None
    if request.user.is_admin_user:
        form = TimetableForm()
        course_id = request.GET.get('course', '')
        entries = Timetable.objects.select_related('subject__course', 'teacher__user')
        if course_id:
            entries = entries.filter(subject__course_id=course_id)
    elif request.user.is_teacher_user:
        teacher = getattr(request.user, 'teacher_profile', None)
        entries = Timetable.objects.filter(teacher=teacher).select_related('subject__course', 'teacher__user')
    else:
        # Student
        student = getattr(request.user, 'student_profile', None)
        if student and student.course:
            entries = Timetable.objects.filter(
                subject__course=student.course,
                subject__semester=student.semester
            ).select_related('subject', 'teacher__user')
        else:
            entries = Timetable.objects.none()

    # Build weekly schedule matrix
    # schedule_matrix[time_label][day] = entry
    schedule_matrix = []
    for start_t, end_t, label in slots:
        row = {'time_label': label, 'days': []}
        for d in days:
            # Match entry starting at slot time or within range
            entry = entries.filter(day_of_week=d, start_time__startswith=start_t[:5]).first()
            row['days'].append(entry)
        schedule_matrix.append(row)

    courses = Course.objects.all() if request.user.is_admin_user else None

    return render(request, 'classroom/timetable.html', {
        'days': day_labels,
        'schedule_matrix': schedule_matrix,
        'form': form,
        'courses': courses,
        'selected_course': request.GET.get('course', ''),
    })


@login_required
@admin_required
def admin_timetable_add(request):
    if request.method == 'POST':
        form = TimetableForm(request.POST)
        if form.is_valid():
            try:
                tt = form.save()
                log_activity(request.user, f"Scheduled {tt.subject.code} on {tt.get_day_of_week_display()} at {tt.start_time}", module="Timetable")
                messages.success(request, "Class scheduled successfully without conflicts.")
            except Exception as e:
                messages.error(request, f"Conflict detected: Room or Teacher is already scheduled at this time.")
        else:
            messages.error(request, "Please correct the form errors.")
    return redirect('admin_timetable')


@login_required
@admin_required
def admin_timetable_delete(request, pk):
    tt = get_object_or_404(Timetable, pk=pk)
    if request.method == 'POST':
        tt.delete()
        log_activity(request.user, "Deleted timetable entry", module="Timetable")
        messages.success(request, "Schedule slot removed.")
    return redirect('admin_timetable')


# ==============================================================================
# ASSIGNMENTS MODULE (SCREEN 9)
# ==============================================================================
@login_required
def assignments_list(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    if request.user.is_admin_user:
        assignments = Assignment.objects.select_related('subject', 'created_by').all()
    elif request.user.is_teacher_user:
        assignments = Assignment.objects.filter(created_by=request.user).select_related('subject')
    else:
        # Student: assignments for student's course and semester
        student = getattr(request.user, 'student_profile', None)
        if student and student.course:
            assignments = Assignment.objects.filter(
                subject__course=student.course,
                subject__semester=student.semester
            ).select_related('subject', 'created_by')
        else:
            assignments = Assignment.objects.none()

    if query:
        assignments = assignments.filter(Q(title__icontains=query) | Q(subject__name__icontains=query) | Q(subject__code__icontains=query))

    # For student, annotate each assignment with their submission status
    student_submissions = {}
    if request.user.is_student_user:
        student = request.user.student_profile
        subs = Submission.objects.filter(student=student)
        for s in subs:
            student_submissions[s.assignment_id] = s

    paginator = Paginator(assignments, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'classroom/assignments.html', {
        'page_obj': page_obj,
        'student_submissions': student_submissions,
        'query': query,
        'today': date.today(),
    })


@login_required
@teacher_required
def teacher_assignment_create(request):
    teacher = getattr(request.user, 'teacher_profile', None)
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.created_by = request.user
            assignment.save()
            log_activity(request.user, f"Created assignment '{assignment.title}' for {assignment.subject.code}", module="Assignments")
            messages.success(request, f"Assignment '{assignment.title}' published successfully.")
            return redirect('teacher_assignments')
        else:
            messages.error(request, "Failed to create assignment. Please check the inputs.")
    else:
        form = AssignmentForm()
        if teacher:
            form.fields['subject'].queryset = Subject.objects.filter(teaching_assignments__teacher=teacher).distinct()

    return render(request, 'classroom/assignment_form.html', {'form': form, 'title': 'Create New Assignment'})


@login_required
@teacher_required
def teacher_assignment_edit(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    if not request.user.is_admin_user and assignment.created_by != request.user:
        messages.error(request, "Permission denied.")
        return redirect('teacher_assignments')

    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, instance=assignment)
        if form.is_valid():
            form.save()
            log_activity(request.user, f"Updated assignment '{assignment.title}'", module="Assignments")
            messages.success(request, "Assignment updated successfully.")
            return redirect('teacher_assignments')
    else:
        form = AssignmentForm(instance=assignment)

    return render(request, 'classroom/assignment_form.html', {'form': form, 'title': f"Edit Assignment - {assignment.title}"})


@login_required
@teacher_required
def teacher_assignment_delete(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    if not request.user.is_admin_user and assignment.created_by != request.user:
        messages.error(request, "Permission denied.")
        return redirect('teacher_assignments')

    if request.method == 'POST':
        title = assignment.title
        assignment.delete()
        log_activity(request.user, f"Deleted assignment '{title}'", module="Assignments")
        messages.success(request, f"Assignment '{title}' deleted.")
    return redirect('teacher_assignments')


@login_required
@student_required
def student_assignment_submit(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    student = request.user.student_profile

    existing_submission = Submission.objects.filter(assignment=assignment, student=student).first()

    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES, instance=existing_submission)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.assignment = assignment
            sub.student = student
            # Mark late if submitted past due date
            if date.today() > assignment.due_date:
                sub.status = Submission.STATUS_LATE
            else:
                sub.status = Submission.STATUS_SUBMITTED
            sub.save()

            log_activity(request.user, f"Submitted assignment '{assignment.title}'", module="Assignments")
            messages.success(request, "Your assignment solution was submitted successfully!")
            return redirect('student_assignments')
        else:
            messages.error(request, "Please attach a valid submission file.")
    else:
        form = SubmissionForm(instance=existing_submission)

    return render(request, 'classroom/assignment_submit.html', {
        'assignment': assignment,
        'submission': existing_submission,
        'form': form,
    })


@login_required
def assignment_submissions(request, pk):
    assignment = get_object_or_404(Assignment.objects.select_related('subject', 'created_by'), pk=pk)
    if request.user.is_student_user:
        messages.error(request, "Unauthorized access.")
        return redirect('student_assignments')

    submissions = assignment.submissions.select_related('student__user').all()

    return render(request, 'classroom/submissions_list.html', {
        'assignment': assignment,
        'submissions': submissions,
    })


@login_required
@teacher_required
def teacher_submissions_all(request):
    """View all pending and graded submissions across teacher assignments."""
    if request.user.is_admin_user:
        submissions = Submission.objects.select_related('assignment__subject', 'student__user').order_by('-submitted_at')
    else:
        submissions = Submission.objects.filter(assignment__created_by=request.user).select_related('assignment__subject', 'student__user').order_by('-submitted_at')

    paginator = Paginator(submissions, 15)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'classroom/teacher_submissions.html', {'page_obj': page_obj})


@login_required
def submission_grade(request, pk):
    submission = get_object_or_404(Submission.objects.select_related('assignment', 'student__user'), pk=pk)
    if request.user.is_student_user:
        messages.error(request, "Unauthorized.")
        return redirect('student_dashboard')

    if request.method == 'POST':
        form = SubmissionGradingForm(request.POST, instance=submission)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.status = Submission.STATUS_GRADED
            sub.save()
            log_activity(request.user, f"Graded assignment for {submission.student.student_id}", module="Assignments")
            messages.success(request, f"Graded student {submission.student.user.display_name} successfully.")
            return redirect('assignment_submissions', pk=submission.assignment.id)
    else:
        form = SubmissionGradingForm(instance=submission)

    return render(request, 'classroom/submission_grade.html', {
        'submission': submission,
        'form': form,
    })


# ==============================================================================
# STUDY MATERIALS MODULE (SCREEN 13)
# ==============================================================================
@login_required
def study_materials_list(request):
    query = request.GET.get('q', '').strip()
    subject_id = request.GET.get('subject', '')

    if request.user.is_admin_user:
        materials = StudyMaterial.objects.select_related('subject', 'uploaded_by').all()
    elif request.user.is_teacher_user:
        materials = StudyMaterial.objects.select_related('subject', 'uploaded_by').all()
    else:
        student = getattr(request.user, 'student_profile', None)
        if student and student.course:
            materials = StudyMaterial.objects.filter(
                subject__course=student.course,
                subject__semester=student.semester
            ).select_related('subject', 'uploaded_by')
        else:
            materials = StudyMaterial.objects.none()

    if query:
        materials = materials.filter(Q(title__icontains=query) | Q(subject__name__icontains=query) | Q(subject__code__icontains=query))
    if subject_id:
        materials = materials.filter(subject_id=subject_id)

    form = None
    if request.user.is_teacher_user or request.user.is_admin_user:
        form = StudyMaterialForm()
        if request.method == 'POST':
            form = StudyMaterialForm(request.POST, request.FILES)
            if form.is_valid():
                mat = form.save(commit=False)
                mat.uploaded_by = request.user
                mat.save()
                log_activity(request.user, f"Uploaded study material '{mat.title}'", module="Study Materials")
                messages.success(request, f"Resource '{mat.title}' uploaded successfully.")
                redirect_url = 'teacher_study_materials' if request.user.is_teacher_user else 'admin_study_materials'
                return redirect(redirect_url)

    subjects = Subject.objects.all()
    paginator = Paginator(materials, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'classroom/study_materials.html', {
        'page_obj': page_obj,
        'form': form,
        'subjects': subjects,
        'selected_subject': subject_id,
        'query': query,
    })


@login_required
def study_material_delete(request, pk):
    mat = get_object_or_404(StudyMaterial, pk=pk)
    if not request.user.is_admin_user and mat.uploaded_by != request.user:
        messages.error(request, "Permission denied.")
        return redirect('study_materials_list')

    if request.method == 'POST':
        title = mat.title
        mat.delete()
        log_activity(request.user, f"Deleted study material '{title}'", module="Study Materials")
        messages.success(request, f"Resource '{title}' deleted.")

    if request.user.is_teacher_user:
        return redirect('teacher_study_materials')
    return redirect('study_materials_list')


# ==============================================================================
# RESULTS & EXAMINATIONS MODULE (SCREEN 10)
# ==============================================================================
@login_required
def results_view(request):
    if request.user.is_student_user:
        student = request.user.student_profile
        semester = request.GET.get('semester', str(student.semester))
        results = Result.objects.filter(student=student, subject__semester=semester).select_related('subject', 'examination')

        # Calculate semester summary
        total_internal = sum(r.internal_marks for r in results)
        total_end_sem = sum(r.end_sem_marks for r in results)
        total_obtained = sum(r.total_marks for r in results)
        total_maximum = sum(r.max_marks for r in results)

        percentage = round((total_obtained / total_maximum * 100), 1) if total_maximum > 0 else 0
        # CGPA approximate (percentage / 9.5 or standard 10 scale)
        cgpa = round((percentage / 10), 2) if percentage > 0 else 0

        # Available semesters for selector
        semesters_range = range(1, (student.course.total_semesters if student.course else 8) + 1)

        return render(request, 'classroom/student_results.html', {
            'student': student,
            'results': results,
            'selected_semester': int(semester),
            'semesters_range': semesters_range,
            'total_internal': total_internal,
            'total_end_sem': total_end_sem,
            'total_obtained': total_obtained,
            'total_maximum': total_maximum,
            'percentage': percentage,
            'cgpa': cgpa,
        })
    else:
        # Teacher or Admin results management
        exams = Examination.objects.all()
        selected_exam_id = request.GET.get('exam', '')
        selected_subject_id = request.GET.get('subject', '')

        results = Result.objects.select_related('student__user', 'subject', 'examination')
        if selected_exam_id:
            results = results.filter(examination_id=selected_exam_id)
        if selected_subject_id:
            results = results.filter(subject_id=selected_subject_id)

        form = ResultForm()
        exam_form = ExaminationForm() if request.user.is_admin_user else None

        paginator = Paginator(results, 15)
        page_obj = paginator.get_page(request.GET.get('page', 1))
        subjects = Subject.objects.all()

        return render(request, 'classroom/results_management.html', {
            'page_obj': page_obj,
            'exams': exams,
            'subjects': subjects,
            'selected_exam': selected_exam_id,
            'selected_subject': selected_subject_id,
            'form': form,
            'exam_form': exam_form,
        })


@login_required
def result_save(request):
    if request.user.is_student_user:
        messages.error(request, "Permission denied.")
        return redirect('student_dashboard')

    if request.method == 'POST':
        form = ResultForm(request.POST)
        if form.is_valid():
            res = form.save()
            log_activity(request.user, f"Recorded exam marks for {res.student.student_id} in {res.subject.code}", module="Results")
            messages.success(request, f"Marks recorded for student {res.student.user.display_name}.")
        else:
            messages.error(request, "Failed to save results. Check marks boundaries.")

    redirect_url = 'teacher_results' if request.user.is_teacher_user else 'admin_results'
    return redirect(redirect_url)


@login_required
@admin_required
def admin_exam_add(request):
    if request.method == 'POST':
        form = ExaminationForm(request.POST)
        if form.is_valid():
            exam = form.save()
            log_activity(request.user, f"Created examination '{exam.name}'", module="Examinations")
            messages.success(request, f"Examination '{exam.name}' created.")
        else:
            messages.error(request, "Failed to create examination.")
    return redirect('admin_results')
