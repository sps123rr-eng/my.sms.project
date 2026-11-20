from django import forms
from .models import LeaveApplication, Notice, FeeRecord, Complaint


class LeaveApplicationForm(forms.ModelForm):
    class Meta:
        model = LeaveApplication
        fields = ['start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'form-control rounded-3', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control rounded-3', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 4, 'placeholder': 'Describe reason for leave (e.g. medical, family function, personal work)...'}),
        }


class LeaveReviewForm(forms.ModelForm):
    class Meta:
        model = LeaveApplication
        fields = ['status', 'admin_remarks']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'admin_remarks': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 3, 'placeholder': 'Optional remarks or approval conditions...'}),
        }


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['title', 'content', 'category', 'audience', 'department', 'attachment', 'is_pinned']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'Announcement title'}),
            'content': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 4, 'placeholder': 'Notice content and details...'}),
            'category': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'audience': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'department': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control rounded-3'}),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FeeRecordForm(forms.ModelForm):
    class Meta:
        model = FeeRecord
        fields = ['student', 'semester', 'title', 'amount', 'due_date', 'status', 'payment_method', 'receipt_number']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'semester': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'min': 1, 'max': 12}),
            'title': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. Semester 4 Tuition & Lab Fees'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'step': '100'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control rounded-3', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. Net Banking / Cheque'}),
            'receipt_number': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'e.g. RCP-2025-001'}),
        }


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['category', 'subject', 'description']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'subject': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'Brief topic of complaint'}),
            'description': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 4, 'placeholder': 'Please detail your grievance or concern...'}),
        }


class ComplaintResponseForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['status', 'admin_response']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'admin_response': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 3, 'placeholder': 'Administrative resolution or action taken...'}),
        }
