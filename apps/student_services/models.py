from django.db import models
from django.core.validators import MinValueValidator, FileExtensionValidator


class LeaveApplication(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='leave_applications')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leaves')
    admin_remarks = models.TextField(blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']

    @property
    def total_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 1

    def __str__(self):
        return f"{self.student.student_id} - Leave ({self.start_date} to {self.end_date}) [{self.get_status_display()}]"


class Notice(models.Model):
    CATEGORY_ACADEMIC = 'ACADEMIC'
    CATEGORY_EXAM = 'EXAM'
    CATEGORY_EVENT = 'EVENT'
    CATEGORY_FINANCE = 'FINANCE'
    CATEGORY_GENERAL = 'GENERAL'

    CATEGORY_CHOICES = [
        (CATEGORY_ACADEMIC, 'Academic'),
        (CATEGORY_EXAM, 'Examination'),
        (CATEGORY_EVENT, 'Event'),
        (CATEGORY_FINANCE, 'Finance'),
        (CATEGORY_GENERAL, 'General Announcement'),
    ]

    AUDIENCE_ALL = 'ALL'
    AUDIENCE_STUDENTS = 'STUDENTS'
    AUDIENCE_TEACHERS = 'TEACHERS'
    AUDIENCE_DEPARTMENT = 'DEPARTMENT'

    AUDIENCE_CHOICES = [
        (AUDIENCE_ALL, 'All Users'),
        (AUDIENCE_STUDENTS, 'Students Only'),
        (AUDIENCE_TEACHERS, 'Teachers Only'),
        (AUDIENCE_DEPARTMENT, 'Specific Department'),
    ]

    title = models.CharField(max_length=250)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_ACADEMIC)
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default=AUDIENCE_ALL)
    department = models.ForeignKey('academics.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='notices')
    published_date = models.DateField(auto_now_add=True)
    author = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='published_notices')
    attachment = models.FileField(
        upload_to='notices/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'png', 'doc', 'docx'])]
    )
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_pinned', '-published_date', '-created_at']

    def __str__(self):
        return f"{self.title} [{self.get_category_display()}]"


class FeeRecord(models.Model):
    STATUS_PAID = 'PAID'
    STATUS_PENDING = 'PENDING'
    STATUS_OVERDUE = 'OVERDUE'
    STATUS_CHOICES = [
        (STATUS_PAID, 'Paid'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_OVERDUE, 'Overdue'),
    ]

    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='fee_records')
    semester = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=150)  # e.g., "Semester 4 Tuition & Lab Fee"
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    due_date = models.DateField()
    paid_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_method = models.CharField(max_length=50, blank=True, null=True)  # Bank Transfer, Cash, DD, Cheque
    receipt_number = models.CharField(max_length=50, blank=True, null=True, unique=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-due_date', 'student']

    @property
    def remaining_amount(self):
        return max(0, self.amount - self.paid_amount)

    def __str__(self):
        return f"{self.student.student_id} - {self.title} - ${self.amount} ({self.get_status_display()})"


class Complaint(models.Model):
    CATEGORY_LIBRARY = 'LIBRARY'
    CATEGORY_HOSTEL = 'HOSTEL'
    CATEGORY_EXAM = 'EXAM'
    CATEGORY_COURSE = 'COURSE'
    CATEGORY_WIFI = 'WIFI'
    CATEGORY_OTHER = 'OTHER'

    CATEGORY_CHOICES = [
        (CATEGORY_LIBRARY, 'Library'),
        (CATEGORY_HOSTEL, 'Room / Hostel Maintenance'),
        (CATEGORY_EXAM, 'Examination Issue'),
        (CATEGORY_COURSE, 'Course / Syllabus Issue'),
        (CATEGORY_WIFI, 'WiFi / Network Issue'),
        (CATEGORY_OTHER, 'Other Grievance'),
    ]

    STATUS_PENDING = 'PENDING'
    STATUS_IN_REVIEW = 'IN_REVIEW'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_REVIEW, 'In-Review'),
        (STATUS_RESOLVED, 'Resolved'),
    ]

    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='complaints')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    admin_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.student_id} - {self.subject} [{self.get_status_display()}]"
