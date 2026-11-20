from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from .models import LeaveApplication, Notice, FeeRecord, Complaint
from .forms import (
    LeaveApplicationForm, LeaveReviewForm, NoticeForm, FeeRecordForm,
    ComplaintForm, ComplaintResponseForm
)
from apps.accounts.permissions import admin_required, teacher_required, student_required
from apps.dashboard.models import log_activity


# ==============================================================================
# LEAVE APPLICATIONS (SCREEN 11)
# ==============================================================================
@login_required
def leaves_list(request):
    if request.user.is_student_user:
        student = request.user.student_profile
        leaves = LeaveApplication.objects.filter(student=student).order_by('-applied_at')
        form = LeaveApplicationForm()

        if request.method == 'POST':
            form = LeaveApplicationForm(request.POST)
            if form.is_valid():
                leave = form.save(commit=False)
                leave.student = student
                leave.save()
                log_activity(request.user, f"Applied for leave from {leave.start_date} to {leave.end_date}", module="Leaves")
                messages.success(request, "Leave application submitted successfully for administrative review.")
                return redirect('student_leave')
            else:
                messages.error(request, "Please check the dates and provide a valid reason.")

        paginator = Paginator(leaves, 10)
        page_obj = paginator.get_page(request.GET.get('page', 1))

        return render(request, 'student_services/student_leaves.html', {
            'page_obj': page_obj,
            'form': form,
        })
    else:
        # Teacher or Admin Review Dashboard
        status_filter = request.GET.get('status', '')
        query = request.GET.get('q', '').strip()

        leaves = LeaveApplication.objects.select_related('student__user').order_by('-applied_at')
        if status_filter:
            leaves = leaves.filter(status=status_filter)
        if query:
            leaves = leaves.filter(
                Q(student__student_id__icontains=query) |
                Q(student__user__first_name__icontains=query) |
                Q(student__user__last_name__icontains=query) |
                Q(reason__icontains=query)
            )

        paginator = Paginator(leaves, 12)
        page_obj = paginator.get_page(request.GET.get('page', 1))

        return render(request, 'student_services/leaves_review.html', {
            'page_obj': page_obj,
            'selected_status': status_filter,
            'query': query,
        })


@login_required
def leave_review(request, pk):
    if request.user.is_student_user:
        messages.error(request, "Permission denied.")
        return redirect('student_dashboard')

    leave = get_object_or_404(LeaveApplication.objects.select_related('student__user'), pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        remarks = request.POST.get('admin_remarks', '').strip()

        if action == 'APPROVE':
            leave.status = LeaveApplication.STATUS_APPROVED
        elif action == 'REJECT':
            leave.status = LeaveApplication.STATUS_REJECTED

        leave.reviewed_by = request.user
        if remarks:
            leave.admin_remarks = remarks
        leave.save()

        log_activity(request.user, f"{action} leave for {leave.student.student_id}", module="Leaves")
        messages.success(request, f"Leave application has been marked as {leave.get_status_display()}.")

    redirect_name = 'teacher_leaves' if request.user.is_teacher_user else 'admin_leaves'
    return redirect(redirect_name)


# ==============================================================================
# NOTICES MODULE (SCREEN 12)
# ==============================================================================
@login_required
def notices_list(request):
    category = request.GET.get('category', '')
    query = request.GET.get('q', '').strip()

    notices = Notice.objects.select_related('author', 'department').all()

    # Filter audience: students only see ALL or STUDENTS or their department
    if request.user.is_student_user:
        student = request.user.student_profile
        notices = notices.filter(
            Q(audience=Notice.AUDIENCE_ALL) |
            Q(audience=Notice.AUDIENCE_STUDENTS) |
            Q(audience=Notice.AUDIENCE_DEPARTMENT, department=student.department)
        )
    elif request.user.is_teacher_user:
        teacher = request.user.teacher_profile
        notices = notices.filter(
            Q(audience=Notice.AUDIENCE_ALL) |
            Q(audience=Notice.AUDIENCE_TEACHERS) |
            Q(audience=Notice.AUDIENCE_DEPARTMENT, department=teacher.department)
        )

    if category:
        notices = notices.filter(category=category)
    if query:
        notices = notices.filter(Q(title__icontains=query) | Q(content__icontains=query))

    form = None
    if not request.user.is_student_user:
        form = NoticeForm()
        if request.method == 'POST':
            form = NoticeForm(request.POST, request.FILES)
            if form.is_valid():
                notice = form.save(commit=False)
                notice.author = request.user
                notice.save()
                log_activity(request.user, f"Published notice: {notice.title}", module="Notices")
                messages.success(request, "Notice published successfully!")
                return redirect(request.path)
            else:
                messages.error(request, "Failed to publish notice. Check inputs.")

    paginator = Paginator(notices, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'student_services/notices.html', {
        'page_obj': page_obj,
        'form': form,
        'selected_category': category,
        'query': query,
    })


@login_required
def notice_delete(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    if not request.user.is_admin_user and notice.author != request.user:
        messages.error(request, "Permission denied.")
        return redirect('notices_list')

    if request.method == 'POST':
        title = notice.title
        notice.delete()
        log_activity(request.user, f"Deleted notice '{title}'", module="Notices")
        messages.success(request, f"Notice '{title}' deleted.")

    if request.user.is_teacher_user:
        return redirect('teacher_notices')
    elif request.user.is_admin_user:
        return redirect('admin_notices')
    return redirect('student_notices')


# ==============================================================================
# FEE MANAGEMENT MODULE (SCREEN 14)
# ==============================================================================
@login_required
def fees_list(request):
    if request.user.is_student_user:
        student = request.user.student_profile
        fees = FeeRecord.objects.filter(student=student).order_by('semester', 'due_date')

        total_due = sum(f.amount for f in fees if f.status != FeeRecord.STATUS_PAID)
        total_paid = sum(f.amount for f in fees if f.status == FeeRecord.STATUS_PAID)

        return render(request, 'student_services/student_fees.html', {
            'fees': fees,
            'student': student,
            'total_due': total_due,
            'total_paid': total_paid,
        })
    else:
        # Admin fee manager
        status_filter = request.GET.get('status', '')
        query = request.GET.get('q', '').strip()

        fees = FeeRecord.objects.select_related('student__user').order_by('-due_date')
        if status_filter:
            fees = fees.filter(status=status_filter)
        if query:
            fees = fees.filter(
                Q(student__student_id__icontains=query) |
                Q(student__user__first_name__icontains=query) |
                Q(student__user__last_name__icontains=query) |
                Q(receipt_number__icontains=query)
            )

        form = FeeRecordForm()
        if request.method == 'POST':
            form = FeeRecordForm(request.POST)
            if form.is_valid():
                fee = form.save()
                log_activity(request.user, f"Generated fee invoice {fee.receipt_number} for {fee.student.student_id}", module="Fees")
                messages.success(request, f"Fee record created successfully.")
                return redirect('admin_fees')
            else:
                messages.error(request, "Failed to create fee record. Verify student and details.")

        paginator = Paginator(fees, 15)
        page_obj = paginator.get_page(request.GET.get('page', 1))

        total_collected = FeeRecord.objects.filter(status=FeeRecord.STATUS_PAID).aggregate(Sum('amount'))['amount__sum'] or 0
        total_pending = FeeRecord.objects.filter(status__in=[FeeRecord.STATUS_PENDING, FeeRecord.STATUS_OVERDUE]).aggregate(Sum('amount'))['amount__sum'] or 0

        return render(request, 'student_services/admin_fees.html', {
            'page_obj': page_obj,
            'form': form,
            'selected_status': status_filter,
            'query': query,
            'total_collected': total_collected,
            'total_pending': total_pending,
        })


@login_required
@admin_required
def admin_fee_mark_paid(request, pk):
    fee = get_object_or_404(FeeRecord, pk=pk)
    if request.method == 'POST':
        fee.status = FeeRecord.STATUS_PAID
        fee.paid_amount = fee.amount
        fee.paid_date = date.today()
        if not fee.receipt_number:
            fee.receipt_number = f"RCP-{date.today().year}-{fee.id:04d}"
        payment_method = request.POST.get('payment_method', 'Bank Transfer / Cash')
        fee.payment_method = payment_method
        fee.save()

        log_activity(request.user, f"Marked fee paid for {fee.student.student_id} (Receipt: {fee.receipt_number})", module="Fees")
        messages.success(request, f"Fee of ${fee.amount} marked as PAID for student {fee.student.user.display_name}.")
    return redirect('admin_fees')


# ==============================================================================
# COMPLAINTS & GRIEVANCES MODULE (SCREEN 15)
# ==============================================================================
@login_required
def complaints_list(request):
    if request.user.is_student_user:
        student = request.user.student_profile
        complaints = Complaint.objects.filter(student=student).order_by('-created_at')
        form = ComplaintForm()

        if request.method == 'POST':
            form = ComplaintForm(request.POST)
            if form.is_valid():
                comp = form.save(commit=False)
                comp.student = student
                comp.save()
                log_activity(request.user, f"Lodged complaint: {comp.subject}", module="Complaints")
                messages.success(request, "Your grievance has been submitted to the administration.")
                return redirect('student_complaints')
            else:
                messages.error(request, "Please enter all complaint details.")

        paginator = Paginator(complaints, 10)
        page_obj = paginator.get_page(request.GET.get('page', 1))

        return render(request, 'student_services/student_complaints.html', {
            'page_obj': page_obj,
            'form': form,
        })
    else:
        # Admin grievance desk
        status_filter = request.GET.get('status', '')
        query = request.GET.get('q', '').strip()

        complaints = Complaint.objects.select_related('student__user').order_by('-created_at')
        if status_filter:
            complaints = complaints.filter(status=status_filter)
        if query:
            complaints = complaints.filter(
                Q(student__student_id__icontains=query) |
                Q(student__user__first_name__icontains=query) |
                Q(subject__icontains=query) |
                Q(description__icontains=query)
            )

        paginator = Paginator(complaints, 12)
        page_obj = paginator.get_page(request.GET.get('page', 1))

        return render(request, 'student_services/admin_complaints.html', {
            'page_obj': page_obj,
            'selected_status': status_filter,
            'query': query,
        })


@login_required
@admin_required
def admin_complaint_respond(request, pk):
    comp = get_object_or_404(Complaint, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status', Complaint.STATUS_RESOLVED)
        response_text = request.POST.get('admin_response', '').strip()

        comp.status = status
        comp.admin_response = response_text
        comp.save()

        log_activity(request.user, f"Responded to grievance '{comp.subject}' with status {comp.get_status_display()}", module="Complaints")
        messages.success(request, f"Grievance status updated to {comp.get_status_display()}.")

    return redirect('admin_complaints')
