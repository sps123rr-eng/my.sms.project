from django.db import models


class AttendanceRecord(models.Model):
    STATUS_PRESENT = 'PRESENT'
    STATUS_ABSENT = 'ABSENT'
    STATUS_LATE = 'LATE'
    STATUS_LEAVE = 'LEAVE'

    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Present'),
        (STATUS_ABSENT, 'Absent'),
        (STATUS_LATE, 'Late'),
        (STATUS_LEAVE, 'Leave'),
    ]

    student = models.ForeignKey(
        'accounts.StudentProfile',
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    subject = models.ForeignKey(
        'academics.Subject',
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PRESENT)
    marked_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_attendances'
    )
    remarks = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'student']
        constraints = [
            models.UniqueConstraint(fields=['student', 'subject', 'date'], name='unique_student_subject_date_attendance')
        ]
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['subject', 'date']),
        ]

    def __str__(self):
        return f"{self.student.student_id} - {self.subject.code} - {self.date} ({self.get_status_display()})"
