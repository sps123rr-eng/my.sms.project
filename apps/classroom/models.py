from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator


class Timetable(models.Model):
    DAY_CHOICES = [
        ('MONDAY', 'Monday'),
        ('TUESDAY', 'Tuesday'),
        ('WEDNESDAY', 'Wednesday'),
        ('THURSDAY', 'Thursday'),
        ('FRIDAY', 'Friday'),
        ('SATURDAY', 'Saturday'),
    ]

    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE, related_name='timetables')
    teacher = models.ForeignKey('accounts.TeacherProfile', on_delete=models.CASCADE, related_name='timetables')
    day_of_week = models.CharField(max_length=15, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=50)
    section = models.CharField(max_length=20, default='A')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']
        constraints = [
            # Prevent same teacher scheduled at same day and time
            models.UniqueConstraint(fields=['teacher', 'day_of_week', 'start_time'], name='unique_teacher_schedule_slot'),
            # Prevent same room booked at same day and time
            models.UniqueConstraint(fields=['room_number', 'day_of_week', 'start_time'], name='unique_room_schedule_slot'),
        ]

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({'end_time': "End time must be after start time."})

    def __str__(self):
        return f"{self.get_day_of_week_display()}: {self.subject.code} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}) Room {self.room_number}"


class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE, related_name='assignments')
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='assignments_created')
    assigned_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    max_marks = models.PositiveIntegerField(default=100, validators=[MinValueValidator(1), MaxValueValidator(1000)])
    attachment = models.FileField(
        upload_to='assignments/tasks/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'zip', 'txt', 'png', 'jpg'])]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-due_date', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.subject.code} (Due: {self.due_date})"


class Submission(models.Model):
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_GRADED = 'GRADED'
    STATUS_LATE = 'LATE'
    STATUS_CHOICES = [
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_GRADED, 'Graded'),
        (STATUS_LATE, 'Late Submission'),
    ]

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='assignment_submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(
        upload_to='assignments/submissions/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'zip', 'txt', 'png', 'jpg', 'py', 'java', 'cpp'])]
    )
    notes = models.TextField(blank=True, null=True)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)

    class Meta:
        ordering = ['-submitted_at']
        constraints = [
            models.UniqueConstraint(fields=['assignment', 'student'], name='unique_assignment_student_submission')
        ]

    def clean(self):
        if self.marks_obtained is not None and self.assignment:
            if self.marks_obtained < 0 or self.marks_obtained > self.assignment.max_marks:
                raise ValidationError({'marks_obtained': f"Marks must be between 0 and {self.assignment.max_marks}."})

    def __str__(self):
        return f"{self.student.student_id} - {self.assignment.title} ({self.get_status_display()})"


class StudyMaterial(models.Model):
    TYPE_PDF = 'PDF'
    TYPE_DOC = 'DOC'
    TYPE_PPT = 'PPT'
    TYPE_ZIP = 'ZIP'
    TYPE_OTHER = 'OTHER'
    TYPE_CHOICES = [
        (TYPE_PDF, 'PDF Document'),
        (TYPE_DOC, 'Word Document'),
        (TYPE_PPT, 'Presentation'),
        (TYPE_ZIP, 'Archive (ZIP)'),
        (TYPE_OTHER, 'Other Document'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE, related_name='study_materials')
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='uploaded_materials')
    file = models.FileField(
        upload_to='study_materials/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'ppt', 'pptx', 'zip', 'txt'])]
    )
    file_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_PDF)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} - {self.subject.code} ({self.file_type})"


class Examination(models.Model):
    TYPE_INTERNAL = 'INTERNAL'
    TYPE_MID_SEM = 'MID_SEM'
    TYPE_END_SEM = 'END_SEM'
    TYPE_CHOICES = [
        (TYPE_INTERNAL, 'Internal Assessment'),
        (TYPE_MID_SEM, 'Mid-Semester Exam'),
        (TYPE_END_SEM, 'End-Semester Exam'),
    ]

    name = models.CharField(max_length=150)
    exam_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_END_SEM)
    session = models.ForeignKey('academics.AcademicSession', on_delete=models.CASCADE, related_name='examinations')
    semester = models.PositiveSmallIntegerField(default=1)
    start_date = models.DateField()
    end_date = models.DateField()
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} (Sem {self.semester})"


class Result(models.Model):
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='results')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE, related_name='results')
    internal_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    end_sem_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    grade = models.CharField(max_length=5, blank=True, null=True)
    remarks = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['examination', 'subject']
        constraints = [
            models.UniqueConstraint(fields=['examination', 'student', 'subject'], name='unique_exam_student_subject_result')
        ]

    def clean(self):
        computed_total = self.internal_marks + self.end_sem_marks
        if computed_total > self.max_marks:
            raise ValidationError(f"Total marks ({computed_total}) cannot exceed maximum marks ({self.max_marks}).")

    def save(self, *args, **kwargs):
        self.total_marks = self.internal_marks + self.end_sem_marks
        if not self.grade:
            pct = (self.total_marks / self.max_marks) * 100 if self.max_marks > 0 else 0
            if pct >= 90:
                self.grade = 'A+'
            elif pct >= 80:
                self.grade = 'A'
            elif pct >= 70:
                self.grade = 'B+'
            elif pct >= 60:
                self.grade = 'B'
            elif pct >= 50:
                self.grade = 'C'
            elif pct >= 40:
                self.grade = 'D'
            else:
                self.grade = 'F'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.student_id} - {self.subject.code} - {self.total_marks}/{self.max_marks} ({self.grade})"
