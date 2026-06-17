from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('SUPERUSER', 'Super User'),
        ('ADMIN', 'Admin'),
        ('SUPERVISOR', 'Supervisor'),
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
    
    closing_date = models.DateField(blank=True, null=True, help_text="Date when project was closed/completed")

    @property
    def remaining_balance(self):
        return self.total_value - self.advances_paid

    def clean(self):
        super().clean()
        if self.status == 'COMPLETED':
            try:
                inv = self.inverter
                if not inv.brand or not inv.model or not inv.serial_number or not inv.capacity:
                    raise ValidationError("A project cannot be completed/closed without complete inverter details (brand, model, serial number, and capacity).")
            except Exception:
                raise ValidationError("A project cannot be completed/closed without inverter details (brand, model, serial number, and capacity).")

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.status == 'COMPLETED' and not self.closing_date:
            from django.utils import timezone
            self.closing_date = timezone.now().date()
        elif self.status != 'COMPLETED':
            self.closing_date = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.customer.username}"


class Inverter(models.Model):
    project = models.OneToOneField(
        SolarInstallationProject,
        on_delete=models.CASCADE,
        related_name='inverter'
    )
    brand = models.CharField(max_length=100, blank=True, null=True, help_text="Inverter Brand")
    model = models.CharField(max_length=100, blank=True, null=True, help_text="Inverter Model")
    serial_number = models.CharField(max_length=100, blank=True, null=True, help_text="Inverter Serial Number (S.No)")
    capacity = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Inverter Capacity in kW")

    def __str__(self):
        return f"{self.brand or 'Unknown'} {self.model or ''} ({self.serial_number or 'No S/N'})"


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


class ProjectExpense(models.Model):
    project = models.ForeignKey(
        SolarInstallationProject,
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='created_expenses'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} - ₹{self.amount} for {self.project.title}"


class LoginLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='login_logs')
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-login_time']

    def __str__(self):
        return f"{self.user.username} logged in at {self.login_time}"


class LeaveRequest(models.Model):
    LEAVE_TYPES = (
        ('CASUAL', 'Casual Leave'),
        ('SICK', 'Sick Leave'),
        ('MEDICAL', 'Medical Leave'),
        ('ANNUAL', 'Annual Leave'),
        ('OTHER', 'Other'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='leave_requests',
        limit_choices_to=models.Q(role='STAFF') | models.Q(role='EMPLOYEE')
    )
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES, default='CASUAL')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves',
        limit_choices_to=models.Q(role='ADMIN') | models.Q(role='SUPERUSER')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.leave_type} ({self.get_status_display()})"


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('INFO', 'Information'),
        ('ACTIVITY', 'Activity Log'),
        ('ALERT', 'Alert / Action Required'),
        ('SUCCESS', 'Success Announcement'),
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='INFO')
    created_at = models.DateTimeField(auto_now_add=True)
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        null=True,
        blank=True,
        help_text="The recipient user. Leave empty for a broadcast to all users."
    )
    is_broadcast = models.BooleanField(default=False, help_text="True if this is a broadcast to everyone.")
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        recipient = "ALL USERS" if self.is_broadcast else (self.user.username if self.user else "System")
        return f"[{self.notification_type}] {self.title} to {recipient}"


class NotificationRead(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='read_notifications')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='reads')
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'notification')

    def __str__(self):
        return f"{self.user.username} read {self.notification.title}"


class Inspection(models.Model):
    STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )
    project = models.ForeignKey(
        SolarInstallationProject, 
        on_delete=models.CASCADE, 
        related_name='inspections'
    )
    scheduled_date = models.DateField(help_text="Scheduled date for the 6-month inspection")
    inspection_date = models.DateField(blank=True, null=True, help_text="Date when inspection was actually performed")
    inspector = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='performed_inspections',
        limit_choices_to={'role': 'STAFF'}
    )
    
    # Checklist
    panel_check = models.BooleanField(default=False, verbose_name="Solar Panels clean and secure")
    inverter_check = models.BooleanField(default=False, verbose_name="Inverter operating correctly")
    wiring_check = models.BooleanField(default=False, verbose_name="Wiring and connections intact")
    mounting_check = models.BooleanField(default=False, verbose_name="Mounting structure stable")
    performance_check = models.BooleanField(default=False, verbose_name="System performance verified")
    
    # Measured Values
    panel_dc_output = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Measured Solar Panel DC Output (kW)")
    inverter_ac_output = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Measured Inverter AC Output (kW)")
    wiring_protection = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Measured Wiring & Protection drop/value")
    earthing_resistance = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Measured Earthing Resistance (ohms)")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    
    # Issue reporting
    has_issues = models.BooleanField(default=False, help_text="Were issues identified during the inspection?")
    issue_details = models.TextField(blank=True, null=True, help_text="Detailed description of the issues reported")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date']

    def clean(self):
        super().clean()
        if self.status == 'COMPLETED':
            limits = InspectionLimit.get_solo()
            
            # Check Panel DC Output
            if self.panel_dc_output is not None:
                if self.panel_dc_output < limits.panel_dc_min or self.panel_dc_output > limits.panel_dc_max:
                    raise ValidationError({
                        'panel_dc_output': f"Solar Panel DC Output ({self.panel_dc_output} kW) must be between {limits.panel_dc_min} and {limits.panel_dc_max} kW."
                    })
            
            # Check Inverter AC Output
            if self.inverter_ac_output is not None:
                if self.inverter_ac_output < limits.inverter_ac_min or self.inverter_ac_output > limits.inverter_ac_max:
                    raise ValidationError({
                        'inverter_ac_output': f"Inverter AC Output ({self.inverter_ac_output} kW) must be between {limits.inverter_ac_min} and {limits.inverter_ac_max} kW."
                    })
            
            # Check Wiring & Protection
            if self.wiring_protection is not None:
                if self.wiring_protection < limits.wiring_protection_min or self.wiring_protection > limits.wiring_protection_max:
                    raise ValidationError({
                        'wiring_protection': f"Wiring and Protections ({self.wiring_protection}) must be between {limits.wiring_protection_min} and {limits.wiring_protection_max}."
                    })
            
            # Check Earthing Resistance
            if self.earthing_resistance is not None:
                if self.earthing_resistance < limits.earthing_resistance_min or self.earthing_resistance > limits.earthing_resistance_max:
                    raise ValidationError({
                        'earthing_resistance': f"Earthing Resistance ({self.earthing_resistance} ohms) must be between {limits.earthing_resistance_min} and {limits.earthing_resistance_max} ohms."
                    })

    def __str__(self):
        return f"6-Month Inspection for {self.project.title} ({self.get_status_display()})"


class InspectionLimit(models.Model):
    panel_dc_min = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    panel_dc_max = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    inverter_ac_min = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    inverter_ac_max = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    wiring_protection_min = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    wiring_protection_max = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    earthing_resistance_min = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    earthing_resistance_max = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):
        return "Supervisor Inspection Limits Configuration"
