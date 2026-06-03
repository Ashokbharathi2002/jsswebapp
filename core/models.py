from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('SUPERUSER', 'Super User'),
        ('ADMIN', 'Admin'),
        ('STAFF', 'Staff'),
        ('EMPLOYEE', 'Employee'),
        ('CUSTOMER', 'Customer'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CUSTOMER')
    is_approved = models.BooleanField(default=False)  # Admin must approve customers before they can log in
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)  # Biodata for Staff/Admin/Employee
    profile_picture_initials = models.CharField(max_length=5, blank=True, null=True)
    
    # Unique ID number for Staff and Employees
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, help_text="Monthly base salary")

    def save(self, *args, **kwargs):
        # Automatically approve Super Users and Admins
        if self.is_superuser or self.role in ['SUPERUSER', 'ADMIN']:
            self.is_approved = True
        
        # Set profile initials if empty
        if not self.profile_picture_initials:
            if self.first_name and self.last_name:
                self.profile_picture_initials = (self.first_name[0] + self.last_name[0]).upper()
            elif self.username:
                self.profile_picture_initials = self.username[:2].upper()
            else:
                self.profile_picture_initials = "U"
                
        # Auto-generate unique ID for STAFF and EMPLOYEE if empty
        if not self.employee_id and self.role in ['STAFF', 'EMPLOYEE']:
            prefix = "STF" if self.role == 'STAFF' else "EMP"
            try:
                # Count existing users in the current role to get a sequence number
                existing_count = CustomUser.objects.filter(role=self.role).count()
                generated_id = f"{prefix}-{1001 + existing_count}"
                while CustomUser.objects.filter(employee_id=generated_id).exists():
                    existing_count += 1
                    generated_id = f"{prefix}-{1001 + existing_count}"
                self.employee_id = generated_id
            except Exception:
                # Fallback if DB queries fail during initial migrations or object creation
                pass
                
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"


class SolarInstallationProject(models.Model):
    STATUS_CHOICES = (
        ('PENDING_APPROVAL', 'Pending Admin Approval'),
        ('SITE_SURVEY', 'Site Survey & Assessment'),
        ('ENGINEERING', 'Engineering & Design'),
        ('PERMITTING', 'Permitting & Documentation'),
        ('INSTALLATION', 'On-site Installation'),
        ('INSPECTION', 'Utility & Safety Inspection'),
        ('INTERCONNECTION', 'Interconnection & Power On'),
        ('COMPLETED', 'Project Completed & Closed'),
    )

    customer = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='solar_projects', 
        limit_choices_to={'role': 'CUSTOMER'}
    )
    staff_incharge = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_projects', 
        limit_choices_to={'role': 'STAFF'}
    )
    title = models.CharField(max_length=150, default="Residential Solar Installation")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING_APPROVAL')
    advances_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)  # Deadline or Completion Date
    laborers_count = models.IntegerField(default=0)  # Number of laborers assisting the staff on-site
    crew_details = models.TextField(blank=True, null=True, help_text="Names and roles of crew members working on-site")

    @property
    def remaining_balance(self):
        return self.total_value - self.advances_paid

    def __str__(self):
        return f"{self.title} - {self.customer.username}"


class Attendance(models.Model):
    STATUS_CHOICES = (
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LEAVE', 'On Leave'),
        ('HALF_DAY', 'Half Day'),
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        limit_choices_to=models.Q(role='STAFF') | models.Q(role='EMPLOYEE')
    )
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PRESENT')
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.get_status_display()}"


class Complaint(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Resolution'),
        ('RESOLVED', 'Resolved & Closed'),
    )
    customer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='complaints',
        limit_choices_to={'role': 'CUSTOMER'}
    )
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.customer.username} - {self.subject} ({self.get_status_display()})"



class Notice(models.Model):
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notices'
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.author.username}"


class Quotation(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent to Client'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    )

    customer = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotations',
        limit_choices_to={'role': 'CUSTOMER'}
    )
    lead_name = models.CharField(max_length=150, blank=True, null=True, help_text="For unregistered leads")
    lead_email = models.EmailField(blank=True, null=True)
    lead_phone = models.CharField(max_length=20, blank=True, null=True)
    
    title = models.CharField(max_length=200, default="Solar System Proposal")
    solar_capacity_kw = models.DecimalField(max_digits=6, decimal_places=2, default=5.00)
    material_breakdown = models.TextField(blank=True, help_text="Details of panels, inverters, etc.")
    
    material_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    labor_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='created_quotations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.total_price or self.total_price == 0:
            self.total_price = self.material_cost + self.labor_cost + self.tax_cost
        super().save(*args, **kwargs)

    def __str__(self):
        client_name = self.customer.get_full_name() if self.customer else self.lead_name
        return f"Quote: {self.title} for {client_name} ({self.solar_capacity_kw}kW)"



