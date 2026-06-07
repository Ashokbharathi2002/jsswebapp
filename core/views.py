from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import HttpResponseForbidden
from django.urls import reverse
from datetime import datetime
from decimal import Decimal
from django.utils import timezone

from .models import CustomUser, SolarInstallationProject, Attendance, Complaint, Notice, Quotation, ProjectExpense
from .forms import (
    CustomerSignUpForm, 
    StaffCreationForm, 
    AdminCreationForm, 
    ProjectForm, 
    StaffProjectUpdateForm,
    AdminCustomerCreationForm,
    StaffSignUpForm,
    StaffEditForm,
    ClientEditForm,
    EmployeeCreationForm,
    EmployeeEditForm,
    ComplaintForm,
    QuotationForm,
    ProjectExpenseForm
)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.role in ['CUSTOMER', 'STAFF', 'EMPLOYEE'] and not user.is_approved:
                # Store the user's username to show on the pending approval page
                request.session['pending_username'] = user.username
                return redirect('pending_approval')
            
            if not user.is_active:
                messages.error(request, "Your account has been deactivated by an Admin.")
                return render(request, 'core/login.html')

            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'core/login.html')
            
    return render(request, 'core/login.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = StaffSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Staff registration successful! Your account is pending Admin approval.")
            request.session['pending_username'] = user.username
            return redirect('pending_approval')
    else:
        form = StaffSignUpForm()
        
    return render(request, 'core/signup.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have logged out successfully.")
    return redirect('login')


def pending_approval(request):
    username = request.session.get('pending_username', 'New Worker')
    return render(request, 'core/pending_approval.html', {'pending_username': username})


@login_required
def dashboard_redirect(request):
    role = request.user.role
    if role == 'SUPERUSER' or request.user.is_superuser:
        return redirect('superuser_dashboard')
    elif role == 'ADMIN':
        return redirect('admin_dashboard')
    elif role == 'STAFF':
        if not request.user.is_approved:
            logout(request)
            return redirect('pending_approval')
        return redirect('staff_dashboard')
    elif role == 'EMPLOYEE':
        if not request.user.is_approved:
            logout(request)
            return redirect('pending_approval')
        return redirect('employee_dashboard')
    elif role == 'CUSTOMER':
        if not request.user.is_approved:
            logout(request)
            return redirect('pending_approval')
        return redirect('customer_dashboard')
    else:
        return redirect('login')


@login_required
def change_password_view(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_new_password = request.POST.get('confirm_new_password')
        
        if not current_password or not new_password or not confirm_new_password:
            messages.error(request, "All password fields are required.")
        elif not request.user.check_password(current_password):
            messages.error(request, "Your current password is incorrect.")
        elif new_password != confirm_new_password:
            messages.error(request, "The new passwords do not match.")
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Your password has been successfully updated!")
            
        next_url = request.META.get('HTTP_REFERER', 'dashboard')
        return redirect(next_url)
    return redirect('dashboard')


@login_required
def customer_dashboard(request):
    if request.user.role != 'CUSTOMER':
        return redirect('dashboard')
    
    if not request.user.is_approved:
        logout(request)
        return redirect('pending_approval')

    # Get the active project for the customer (if any)
    projects = SolarInstallationProject.objects.filter(customer=request.user).order_by('-id')
    active_project = projects.first()

    complaints = Complaint.objects.filter(customer=request.user).order_by('-id')
    complaint_form = ComplaintForm()

    # Get project expenses for client
    expenses = ProjectExpense.objects.filter(project__customer=request.user).order_by('-date', '-id')
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0.00

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'raise_complaint':
            form = ComplaintForm(request.POST)
            if form.is_valid():
                complaint = form.save(commit=False)
                complaint.customer = request.user
                complaint.save()
                messages.success(request, "Your complaint has been successfully registered. Jothi Solar Solutions admins will address it shortly.")
                return redirect('customer_dashboard')
            else:
                messages.error(request, "Failed to register complaint. Please verify inputs.")

    context = {
        'project': active_project,
        'has_project': active_project is not None,
        'complaints': complaints,
        'complaint_form': complaint_form,
        'expenses': expenses,
        'total_expenses': total_expenses,
    }
    return render(request, 'core/customer_dashboard.html', context)


@login_required
def staff_dashboard(request):
    if request.user.role != 'STAFF':
        return redirect('dashboard')

    staff_user = request.user
    
    # Track and display:
    # 1. Number of clients actively handling (status is NOT Completed/Pending Approval)
    active_projects = SolarInstallationProject.objects.filter(
        staff_incharge=staff_user
    ).exclude(status__in=['COMPLETED', 'PENDING_APPROVAL'])
    active_clients_count = active_projects.values('customer').distinct().count()

    # 2. Number of clients successfully closed (status IS Completed)
    closed_projects = SolarInstallationProject.objects.filter(
        staff_incharge=staff_user, status='COMPLETED'
    )
    closed_clients_count = closed_projects.values('customer').distinct().count()

    # 3. Total value of the active projects assigned to them
    total_assigned_value = SolarInstallationProject.objects.filter(
        staff_incharge=staff_user
    ).exclude(status='COMPLETED').aggregate(Sum('total_value'))['total_value__sum'] or 0.00

    # 4. Total number of laborers assisting them on-site currently
    total_laborers = active_projects.aggregate(Sum('laborers_count'))['laborers_count__sum'] or 0

    # Load attendance records
    attendance_records = Attendance.objects.filter(user=staff_user).order_by('-date')
    total_days = attendance_records.count()
    present_days = attendance_records.filter(status='PRESENT').count()
    rating_pct = (present_days / total_days * 100) if total_days > 0 else 100.0

    calculated_salary_overall = Decimal(float(staff_user.salary or 0.00) * (rating_pct / 100.0))

    # Monthly
    now = timezone.now()
    total_days_monthly = Attendance.objects.filter(user=staff_user, date__year=now.year, date__month=now.month).count()
    present_days_monthly = Attendance.objects.filter(user=staff_user, status='PRESENT', date__year=now.year, date__month=now.month).count()
    rating_pct_monthly = (present_days_monthly / total_days_monthly * 100) if total_days_monthly > 0 else 100.0
    calculated_salary_monthly = Decimal(float(staff_user.salary or 0.00) * (rating_pct_monthly / 100.0))

    # Project updates processing (Staff updating progress/laborers/crew)
    if request.method == 'POST':
        project_id = request.POST.get('project_id')
        project = get_object_or_404(SolarInstallationProject, id=project_id, staff_incharge=staff_user)
        form = StaffProjectUpdateForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated progress for project '{project.title}' successfully!")
            return redirect('staff_dashboard')
    # Prepopulate updates forms for active projects
    forms_list = []
    for proj in active_projects:
        forms_list.append({
            'project': proj,
            'form': StaffProjectUpdateForm(instance=proj)
        })

    # Project Expenses
    expenses = ProjectExpense.objects.filter(project__staff_incharge=staff_user).order_by('-date', '-id')
    expense_projects = SolarInstallationProject.objects.filter(staff_incharge=staff_user).order_by('-id')
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0.00

    context = {
        'active_clients_count': active_clients_count,
        'closed_clients_count': closed_clients_count,
        'total_assigned_value': total_assigned_value,
        'total_laborers': total_laborers,
        'active_projects': active_projects,
        'closed_projects': closed_projects,
        'project_update_forms': forms_list if 'forms_list' in locals() else [],
        'attendance_records': attendance_records[:15],
        'attendance_rating_pct': rating_pct,
        'rating_pct_overall': rating_pct,
        'calculated_salary_overall': calculated_salary_overall,
        'rating_pct_monthly': rating_pct_monthly,
        'calculated_salary_monthly': calculated_salary_monthly,
        'current_month_name': now.strftime('%B'),
        'expenses': expenses,
        'expense_projects': expense_projects,
        'total_expenses': total_expenses,
    }
    return render(request, 'core/staff_dashboard.html', context)


@login_required
def employee_dashboard(request):
    if request.user.role != 'EMPLOYEE':
        return redirect('dashboard')
        
    employee_user = request.user
    
    # Intelligently find if they are part of active projects
    # (By checking if their username or employee_id is in the crew_details)
    active_projects = SolarInstallationProject.objects.filter(
        Q(crew_details__icontains=employee_user.username) |
        Q(crew_details__icontains=employee_user.employee_id)
    ).exclude(status__in=['COMPLETED', 'PENDING_APPROVAL'])
    
    # Attendance metrics
    attendance_records = Attendance.objects.filter(user=employee_user).order_by('-date')
    total_days = attendance_records.count()
    present_days = attendance_records.filter(status='PRESENT').count()
    rating_pct = (present_days / total_days * 100) if total_days > 0 else 100.0

    calculated_salary_overall = Decimal(float(employee_user.salary or 0.00) * (rating_pct / 100.0))

    # Monthly
    now = timezone.now()
    total_days_monthly = Attendance.objects.filter(user=employee_user, date__year=now.year, date__month=now.month).count()
    present_days_monthly = Attendance.objects.filter(user=employee_user, status='PRESENT', date__year=now.year, date__month=now.month).count()
    rating_pct_monthly = (present_days_monthly / total_days_monthly * 100) if total_days_monthly > 0 else 100.0
    calculated_salary_monthly = Decimal(float(employee_user.salary or 0.00) * (rating_pct_monthly / 100.0))
    
    context = {
        'active_projects': active_projects,
        'attendance_records': attendance_records[:15],
        'attendance_rating_pct': rating_pct,
        'rating_pct_overall': rating_pct,
        'calculated_salary_overall': calculated_salary_overall,
        'rating_pct_monthly': rating_pct_monthly,
        'calculated_salary_monthly': calculated_salary_monthly,
        'current_month_name': now.strftime('%B'),
    }
    return render(request, 'core/employee_dashboard.html', context)


@login_required
def admin_dashboard(request):
    if request.user.role not in ['ADMIN', 'SUPERUSER'] and not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: Admins Only")

    # Metrics
    total_clients = CustomUser.objects.filter(role='CUSTOMER').count()
    active_installations = SolarInstallationProject.objects.exclude(status__in=['COMPLETED', 'PENDING_APPROVAL']).count()
    completed_installations = SolarInstallationProject.objects.filter(status='COMPLETED').count()
    pending_approvals_count = CustomUser.objects.filter(role__in=['CUSTOMER', 'STAFF', 'EMPLOYEE'], is_approved=False).count()

    # Database query collections for management tabs
    pending_users = CustomUser.objects.filter(role__in=['CUSTOMER', 'STAFF', 'EMPLOYEE'], is_approved=False).order_by('-date_joined')
    staff_members = CustomUser.objects.filter(role='STAFF').order_by('username')
    employees_members = CustomUser.objects.filter(role='EMPLOYEE').order_by('username')

    # Worker search query based on name or employee ID
    worker_search = request.GET.get('worker_search', '').strip()
    if worker_search:
        staff_members = staff_members.filter(
            Q(username__icontains=worker_search) |
            Q(first_name__icontains=worker_search) |
            Q(last_name__icontains=worker_search) |
            Q(employee_id__icontains=worker_search)
        )
        employees_members = employees_members.filter(
            Q(username__icontains=worker_search) |
            Q(first_name__icontains=worker_search) |
            Q(last_name__icontains=worker_search) |
            Q(employee_id__icontains=worker_search)
        )

    # Pre-populate Client details list with edit forms
    customer_data_list = []
    for customer in CustomUser.objects.filter(role='CUSTOMER').order_by('username'):
        customer_data_list.append({
            'customer': customer,
            'edit_form': ClientEditForm(instance=customer)
        })
        
    # Pre-populate Project details list with edit forms
    project_data_list = []
    for proj in SolarInstallationProject.objects.all().order_by('-start_date'):
        project_data_list.append({
            'project': proj,
            'edit_form': ProjectForm(instance=proj)
        })

    # Pre-populate Staff list
    staff_data_list = []
    for staff in staff_members:
        completed_count = SolarInstallationProject.objects.filter(staff_incharge=staff, status='COMPLETED').count()
        active_projs = SolarInstallationProject.objects.filter(staff_incharge=staff).exclude(status__in=['COMPLETED', 'PENDING_APPROVAL'])
        active_count = active_projs.count()
        current_assigned_project = active_projs.first()
        
        crew_details_list = []
        for p in active_projs:
            if p.crew_details:
                crew_details_list.append(f"{p.title}: {p.crew_details} ({p.laborers_count} laborers)")

        # Salary calculations
        total_days = Attendance.objects.filter(user=staff).count()
        present_days = Attendance.objects.filter(user=staff, status='PRESENT').count()
        rating_pct = (present_days / total_days * 100) if total_days > 0 else 100.0
        calculated_salary_overall = Decimal(float(staff.salary or 0.00) * (rating_pct / 100.0))

        # Monthly
        now = timezone.now()
        total_days_monthly = Attendance.objects.filter(user=staff, date__year=now.year, date__month=now.month).count()
        present_days_monthly = Attendance.objects.filter(user=staff, status='PRESENT', date__year=now.year, date__month=now.month).count()
        rating_pct_monthly = (present_days_monthly / total_days_monthly * 100) if total_days_monthly > 0 else 100.0
        calculated_salary_monthly = Decimal(float(staff.salary or 0.00) * (rating_pct_monthly / 100.0))

        staff_data_list.append({
            'staff': staff,
            'completed_count': completed_count,
            'active_count': active_count,
            'current_project': current_assigned_project,
            'crew_summary': ", ".join(crew_details_list) if crew_details_list else "No active crew assigned",
            'edit_form': StaffEditForm(instance=staff),
            'rating_pct_overall': rating_pct,
            'calculated_salary_overall': calculated_salary_overall,
            'rating_pct_monthly': rating_pct_monthly,
            'calculated_salary_monthly': calculated_salary_monthly,
        })

    # Pre-populate Employees list with edit forms
    employees_data_list = []
    for emp in employees_members:
        # Check active crew allocations
        active_crews = SolarInstallationProject.objects.filter(
            Q(crew_details__icontains=emp.username) | Q(crew_details__icontains=emp.employee_id)
        ).exclude(status__in=['COMPLETED', 'PENDING_APPROVAL'])

        # Salary calculations
        total_days = Attendance.objects.filter(user=emp).count()
        present_days = Attendance.objects.filter(user=emp, status='PRESENT').count()
        rating_pct = (present_days / total_days * 100) if total_days > 0 else 100.0
        calculated_salary_overall = Decimal(float(emp.salary or 0.00) * (rating_pct / 100.0))

        # Monthly
        now = timezone.now()
        total_days_monthly = Attendance.objects.filter(user=emp, date__year=now.year, date__month=now.month).count()
        present_days_monthly = Attendance.objects.filter(user=emp, status='PRESENT', date__year=now.year, date__month=now.month).count()
        rating_pct_monthly = (present_days_monthly / total_days_monthly * 100) if total_days_monthly > 0 else 100.0
        calculated_salary_monthly = Decimal(float(emp.salary or 0.00) * (rating_pct_monthly / 100.0))
        
        employees_data_list.append({
            'employee': emp,
            'active_project_count': active_crews.count(),
            'current_project_summary': ", ".join([p.title for p in active_crews]) if active_crews.exists() else "Unassigned",
            'edit_form': EmployeeEditForm(instance=emp),
            'rating_pct_overall': rating_pct,
            'calculated_salary_overall': calculated_salary_overall,
            'rating_pct_monthly': rating_pct_monthly,
            'calculated_salary_monthly': calculated_salary_monthly,
        })

    # Load Attendance list for selected date
    attendance_date_str = request.GET.get('date')
    try:
        attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        attendance_date = datetime.today().date()
        attendance_date_str = attendance_date.strftime('%Y-%m-%d')

    workers = CustomUser.objects.filter(role__in=['STAFF', 'EMPLOYEE']).order_by('role', 'username')
    attendance_data = []
    for worker in workers:
        att_record = Attendance.objects.filter(user=worker, date=attendance_date).first()
        attendance_data.append({
            'worker': worker,
            'status': att_record.status if att_record else 'PRESENT',
            'notes': att_record.notes if att_record else ''
        })

    # Attendance overall ratings
    attendance_stats = []
    for worker in workers:
        total_days = Attendance.objects.filter(user=worker).count()
        present_days = Attendance.objects.filter(user=worker, status='PRESENT').count()
        rating_pct = (present_days / total_days * 100) if total_days > 0 else 100.0
        
        calculated_salary_overall = Decimal(float(worker.salary or 0.00) * (rating_pct / 100.0))
        
        # Monthly
        now = timezone.now()
        total_days_monthly = Attendance.objects.filter(user=worker, date__year=now.year, date__month=now.month).count()
        present_days_monthly = Attendance.objects.filter(user=worker, status='PRESENT', date__year=now.year, date__month=now.month).count()
        rating_pct_monthly = (present_days_monthly / total_days_monthly * 100) if total_days_monthly > 0 else 100.0
        calculated_salary_monthly = Decimal(float(worker.salary or 0.00) * (rating_pct_monthly / 100.0))

        attendance_stats.append({
            'worker': worker,
            'total_days': total_days,
            'present_days': present_days,
            'rating_pct': rating_pct,
            'calculated_salary_overall': calculated_salary_overall,
            'rating_pct_monthly': rating_pct_monthly,
            'calculated_salary_monthly': calculated_salary_monthly,
        })

    # Form handling
    project_form = ProjectForm()
    staff_form = StaffCreationForm()
    employee_form = EmployeeCreationForm()
    customer_form = AdminCustomerCreationForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_project':
            form = ProjectForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Solar project configured successfully!")
                return redirect('admin_dashboard')
            else:
                project_form = form
                messages.error(request, "Failed to create project. Please verify inputs.")
        elif action == 'create_staff':
            form = StaffCreationForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "New staff account created successfully!")
                return redirect('admin_dashboard')
            else:
                staff_form = form
                messages.error(request, "Failed to create staff. Please verify username/fields.")
        elif action == 'create_employee':
            form = EmployeeCreationForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "New employee account created successfully!")
                return redirect('admin_dashboard')
            else:
                employee_form = form
                messages.error(request, "Failed to create employee. Please verify details.")
        elif action == 'create_customer':
            form = AdminCustomerCreationForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "New customer account registered successfully!")
                return redirect('admin_dashboard')
            else:
                customer_form = form
                messages.error(request, "Failed to create customer. Please verify username/fields.")
        elif action == 'edit_staff':
            staff_id = request.POST.get('staff_id')
            staff_member = get_object_or_404(CustomUser, id=staff_id, role='STAFF')
            form = StaffEditForm(request.POST, instance=staff_member)
            if form.is_valid():
                form.save()
                messages.success(request, f"Worker '{staff_member.username}' details updated successfully!")
                return redirect('admin_dashboard')
            else:
                messages.error(request, "Failed to update staff details.")
        elif action == 'edit_employee':
            emp_id = request.POST.get('worker_id')
            emp_member = get_object_or_404(CustomUser, id=emp_id, role='EMPLOYEE')
            form = EmployeeEditForm(request.POST, instance=emp_member)
            if form.is_valid():
                form.save()
                messages.success(request, f"Employee '{emp_member.username}' details updated successfully!")
                return redirect('admin_dashboard')
            else:
                messages.error(request, "Failed to update employee details.")
        elif action == 'edit_customer':
            customer_id = request.POST.get('customer_id')
            customer_member = get_object_or_404(CustomUser, id=customer_id, role='CUSTOMER')
            form = ClientEditForm(request.POST, instance=customer_member)
            if form.is_valid():
                form.save()
                messages.success(request, f"Customer '{customer_member.username}' details updated successfully!")
                return redirect('admin_dashboard')
            else:
                messages.error(request, "Failed to update customer details.")
        elif action == 'edit_project':
            project_id = request.POST.get('project_id')
            project = get_object_or_404(SolarInstallationProject, id=project_id)
            form = ProjectForm(request.POST, instance=project)
            if form.is_valid():
                form.save()
                messages.success(request, f"Project '{project.title}' (Progress Tracker) updated successfully!")
                return redirect('admin_dashboard')
            else:
                messages.error(request, "Failed to update project details.")
        elif action == 'mark_attendance':
            date_str = request.POST.get('attendance_date')
            try:
                att_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                att_date = datetime.today().date()
                date_str = att_date.strftime('%Y-%m-%d')
            
            for worker in workers:
                status_key = f"status_{worker.id}"
                notes_key = f"notes_{worker.id}"
                status_val = request.POST.get(status_key)
                notes_val = request.POST.get(notes_key, '')
                if status_val:
                    Attendance.objects.update_or_create(
                        user=worker,
                        date=att_date,
                        defaults={'status': status_val, 'notes': notes_val}
                    )
            messages.success(request, f"Attendance successfully marked for {att_date.strftime('%b %d, %Y')}!")
            return redirect(f"{reverse('admin_dashboard')}?date={date_str}")
        elif action == 'close_project':
            project_id = request.POST.get('project_id')
            project = get_object_or_404(SolarInstallationProject, id=project_id)
            project.status = 'COMPLETED'
            project.save()
            messages.success(request, f"Solar project '{project.title}' has been successfully completed and closed!")
            return redirect('admin_dashboard')
        elif action == 'resolve_complaint':
            complaint_id = request.POST.get('complaint_id')
            complaint = get_object_or_404(Complaint, id=complaint_id)
            complaint.status = 'RESOLVED'
            complaint.resolved_at = timezone.now()
            complaint.save()
            messages.success(request, f"Complaint by customer '{complaint.customer.username}' has been marked as resolved!")
            return redirect('admin_dashboard')
        elif action == 'reset_password':
            user_id = request.POST.get('user_id')
            user_instance = get_object_or_404(CustomUser, id=user_id)
            if user_instance.role not in ['STAFF', 'EMPLOYEE', 'CUSTOMER']:
                messages.error(request, "Permission Denied: Admins can only reset passwords for staff, employees, and customers.")
            else:
                new_password = request.POST.get('new_password')
                if new_password:
                    user_instance.set_password(new_password)
                    user_instance.save()
                    messages.success(request, f"Password for '{user_instance.username}' has been successfully reset!")
                else:
                    messages.error(request, "Password cannot be empty.")
            return redirect('admin_dashboard')

    pending_complaints = Complaint.objects.filter(status='PENDING').order_by('-created_at')
    resolved_complaints = Complaint.objects.filter(status='RESOLVED').order_by('-resolved_at')
    pending_complaints_count = pending_complaints.count()
    # Project Expenses
    expenses = ProjectExpense.objects.all().order_by('-date', '-id')
    expense_projects = SolarInstallationProject.objects.all().order_by('-id')
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0.00

    context = {
        'total_clients': total_clients,
        'active_installations': active_installations,
        'completed_installations': completed_installations,
        'pending_approvals_count': pending_approvals_count,
        'pending_customers': pending_users,
        'all_customers': customer_data_list,
        'staff_data_list': staff_data_list,
        'employees_data_list': employees_data_list,
        'all_projects': project_data_list,
        'project_form': project_form,
        'staff_form': staff_form,
        'employee_form': employee_form,
        'customer_form': customer_form,
        
        # Attendance params
        'attendance_data': attendance_data,
        'attendance_date_str': attendance_date_str,
        'attendance_stats': attendance_stats,
        
        # Complaints params
        'pending_complaints': pending_complaints,
        'resolved_complaints': resolved_complaints,
        'pending_complaints_count': pending_complaints_count,
        
        # Worker search
        'worker_search': worker_search,
        'current_month_name': timezone.now().strftime('%B'),
        
        # Project Expenses
        'expenses': expenses,
        'expense_projects': expense_projects,
        'total_expenses': total_expenses,
    }
    return render(request, 'core/admin_dashboard.html', context)


@login_required
def superuser_dashboard(request):
    if request.user.role != 'SUPERUSER' and not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: Super Users Only")

    # Prepopulate lists with edit forms
    # 1. Admins list
    admins_list = []
    for admin in CustomUser.objects.filter(role='ADMIN').order_by('username'):
        admins_list.append({
            'admin': admin,
            'edit_form': StaffEditForm(instance=admin)  # Reuse StaffEditForm for Admin edit
        })

    # 2. Staff list
    staff_members = CustomUser.objects.filter(role='STAFF').order_by('username')
    # 3. Employee list
    employees_members = CustomUser.objects.filter(role='EMPLOYEE').order_by('username')

    # Worker search query based on name or employee ID
    worker_search = request.GET.get('worker_search', '').strip()
    if worker_search:
        staff_members = staff_members.filter(
            Q(username__icontains=worker_search) |
            Q(first_name__icontains=worker_search) |
            Q(last_name__icontains=worker_search) |
            Q(employee_id__icontains=worker_search)
        )
        employees_members = employees_members.filter(
            Q(username__icontains=worker_search) |
            Q(first_name__icontains=worker_search) |
            Q(last_name__icontains=worker_search) |
            Q(employee_id__icontains=worker_search)
        )

    staff_data_list = []
    for staff in staff_members:
        completed_count = SolarInstallationProject.objects.filter(staff_incharge=staff, status='COMPLETED').count()
        active_projs = SolarInstallationProject.objects.filter(staff_incharge=staff).exclude(status__in=['COMPLETED', 'PENDING_APPROVAL'])
        active_count = active_projs.count()
        current_assigned_project = active_projs.first()
        crew_details_list = []
        for p in active_projs:
            if p.crew_details:
                crew_details_list.append(f"{p.title}: {p.crew_details} ({p.laborers_count} laborers)")

        # Salary calculations
        total_days = Attendance.objects.filter(user=staff).count()
        present_days = Attendance.objects.filter(user=staff, status='PRESENT').count()
        rating_pct = (present_days / total_days * 100) if total_days > 0 else 100.0
        calculated_salary_overall = Decimal(float(staff.salary or 0.00) * (rating_pct / 100.0))

        # Monthly
        now = timezone.now()
        total_days_monthly = Attendance.objects.filter(user=staff, date__year=now.year, date__month=now.month).count()
        present_days_monthly = Attendance.objects.filter(user=staff, status='PRESENT', date__year=now.year, date__month=now.month).count()
        rating_pct_monthly = (present_days_monthly / total_days_monthly * 100) if total_days_monthly > 0 else 100.0
        calculated_salary_monthly = Decimal(float(staff.salary or 0.00) * (rating_pct_monthly / 100.0))

        staff_data_list.append({
            'staff': staff,
            'completed_count': completed_count,
            'active_count': active_count,
            'current_project': current_assigned_project,
            'crew_summary': ", ".join(crew_details_list) if crew_details_list else "No active crew assigned",
            'edit_form': StaffEditForm(instance=staff),
            'rating_pct_overall': rating_pct,
            'calculated_salary_overall': calculated_salary_overall,
            'rating_pct_monthly': rating_pct_monthly,
            'calculated_salary_monthly': calculated_salary_monthly,
        })

    employees_data_list = []
    for emp in employees_members:
        active_crews = SolarInstallationProject.objects.filter(
            Q(crew_details__icontains=emp.username) | Q(crew_details__icontains=emp.employee_id)
        ).exclude(status__in=['COMPLETED', 'PENDING_APPROVAL'])
        
        # Salary calculations
        total_days = Attendance.objects.filter(user=emp).count()
        present_days = Attendance.objects.filter(user=emp, status='PRESENT').count()
        rating_pct = (present_days / total_days * 100) if total_days > 0 else 100.0
        calculated_salary_overall = Decimal(float(emp.salary or 0.00) * (rating_pct / 100.0))

        # Monthly
        now = timezone.now()
        total_days_monthly = Attendance.objects.filter(user=emp, date__year=now.year, date__month=now.month).count()
        present_days_monthly = Attendance.objects.filter(user=emp, status='PRESENT', date__year=now.year, date__month=now.month).count()
        rating_pct_monthly = (present_days_monthly / total_days_monthly * 100) if total_days_monthly > 0 else 100.0
        calculated_salary_monthly = Decimal(float(emp.salary or 0.00) * (rating_pct_monthly / 100.0))

        employees_data_list.append({
            'employee': emp,
            'active_project_count': active_crews.count(),
            'current_project_summary': ", ".join([p.title for p in active_crews]) if active_crews.exists() else "Unassigned",
            'edit_form': EmployeeEditForm(instance=emp),
            'rating_pct_overall': rating_pct,
            'calculated_salary_overall': calculated_salary_overall,
            'rating_pct_monthly': rating_pct_monthly,
            'calculated_salary_monthly': calculated_salary_monthly,
        })

    # 4. Customer list
    customer_data_list = []
    for customer in CustomUser.objects.filter(role='CUSTOMER').order_by('username'):
        customer_data_list.append({
            'customer': customer,
            'edit_form': ClientEditForm(instance=customer)
        })

    # 5. Project list
    project_data_list = []
    for proj in SolarInstallationProject.objects.all().order_by('-start_date'):
        project_data_list.append({
            'project': proj,
            'edit_form': ProjectForm(instance=proj)
        })

    # Load Attendance list for selected date
    attendance_date_str = request.GET.get('date')
    try:
        attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        attendance_date = datetime.today().date()
        attendance_date_str = attendance_date.strftime('%Y-%m-%d')

    workers = CustomUser.objects.filter(role__in=['STAFF', 'EMPLOYEE']).order_by('role', 'username')
    attendance_data = []
    for worker in workers:
        att_record = Attendance.objects.filter(user=worker, date=attendance_date).first()
        attendance_data.append({
            'worker': worker,
            'status': att_record.status if att_record else 'PRESENT',
            'notes': att_record.notes if att_record else ''
        })

    # Attendance overall ratings
    attendance_stats = []
    for worker in workers:
        total_days = Attendance.objects.filter(user=worker).count()
        present_days = Attendance.objects.filter(user=worker, status='PRESENT').count()
        rating_pct = (present_days / total_days * 100) if total_days > 0 else 100.0

        calculated_salary_overall = Decimal(float(worker.salary or 0.00) * (rating_pct / 100.0))

        # Monthly
        now = timezone.now()
        total_days_monthly = Attendance.objects.filter(user=worker, date__year=now.year, date__month=now.month).count()
        present_days_monthly = Attendance.objects.filter(user=worker, status='PRESENT', date__year=now.year, date__month=now.month).count()
        rating_pct_monthly = (present_days_monthly / total_days_monthly * 100) if total_days_monthly > 0 else 100.0
        calculated_salary_monthly = Decimal(float(worker.salary or 0.00) * (rating_pct_monthly / 100.0))

        attendance_stats.append({
            'worker': worker,
            'total_days': total_days,
            'present_days': present_days,
            'rating_pct': rating_pct,
            'calculated_salary_overall': calculated_salary_overall,
            'rating_pct_monthly': rating_pct_monthly,
            'calculated_salary_monthly': calculated_salary_monthly,
        })

    # POST Handling
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_admin':
            form = AdminCreationForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "New Admin created successfully!")
                return redirect('superuser_dashboard')
            else:
                messages.error(request, "Failed to create Admin. Please verify details.")
                
        elif action == 'create_staff':
            form = StaffCreationForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "New staff account created successfully!")
                return redirect('superuser_dashboard')
            else:
                messages.error(request, "Failed to create staff. Please verify details.")

        elif action == 'create_employee':
            form = EmployeeCreationForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "New employee account created successfully!")
                return redirect('superuser_dashboard')
            else:
                messages.error(request, "Failed to create employee. Please verify details.")

        elif action == 'create_customer':
            form = AdminCustomerCreationForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "New customer account registered successfully!")
                return redirect('superuser_dashboard')
            else:
                messages.error(request, "Failed to register customer account. Verify details.")

        elif action == 'create_project':
            form = ProjectForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Solar project configured successfully!")
                return redirect('superuser_dashboard')
            else:
                messages.error(request, "Failed to create project. Please verify inputs.")

        elif action == 'edit_admin':
            admin_id = request.POST.get('admin_id')
            admin_member = get_object_or_404(CustomUser, id=admin_id, role='ADMIN')
            form = StaffEditForm(request.POST, instance=admin_member)
            if form.is_valid():
                form.save()
                messages.success(request, f"Admin '{admin_member.username}' details updated successfully!")
                return redirect('superuser_dashboard')
            else:
                messages.error(request, "Failed to update admin details.")

        elif action == 'edit_staff':
            staff_id = request.POST.get('staff_id')
            staff_member = get_object_or_404(CustomUser, id=staff_id, role='STAFF')
            form = StaffEditForm(request.POST, instance=staff_member)
            if form.is_valid():
                form.save()
                messages.success(request, f"Worker '{staff_member.username}' details updated successfully!")
                return redirect('superuser_dashboard')
            else:
                messages.error(request, "Failed to update staff details.")

        elif action == 'edit_employee':
            emp_id = request.POST.get('worker_id')
            emp_member = get_object_or_404(CustomUser, id=emp_id, role='EMPLOYEE')
            form = EmployeeEditForm(request.POST, instance=emp_member)
            if form.is_valid():
                form.save()
                messages.success(request, f"Employee '{emp_member.username}' details updated successfully!")
                return redirect('superuser_dashboard')
            else:
                messages.error(request, "Failed to update employee details.")

        elif action == 'edit_customer':
            customer_id = request.POST.get('customer_id')
            customer_member = get_object_or_404(CustomUser, id=customer_id, role='CUSTOMER')
            form = ClientEditForm(request.POST, instance=customer_member)
            if form.is_valid():
                form.save()
                messages.success(request, f"Customer '{customer_member.username}' details updated successfully!")
                return redirect('superuser_dashboard')
            else:
                messages.error(request, "Failed to update customer details.")

        elif action == 'edit_project':
            project_id = request.POST.get('project_id')
            project = get_object_or_404(SolarInstallationProject, id=project_id)
            form = ProjectForm(request.POST, instance=project)
            if form.is_valid():
                form.save()
                messages.success(request, f"Project '{project.title}' (Progress Tracker) updated successfully!")
                return redirect('superuser_dashboard')
            else:
                messages.error(request, "Failed to update project details.")

        elif action == 'reset_password':
            user_id = request.POST.get('user_id')
            user_instance = get_object_or_404(CustomUser, id=user_id)
            new_password = request.POST.get('new_password')
            if new_password:
                user_instance.set_password(new_password)
                user_instance.save()
                messages.success(request, f"Password for '{user_instance.username}' has been successfully reset!")
            else:
                messages.error(request, "Password cannot be empty.")
            return redirect('superuser_dashboard')
        elif action == 'delete_user':
            user_id = request.POST.get('user_id')
            user_to_delete = get_object_or_404(CustomUser, id=user_id)
            if user_to_delete == request.user:
                messages.error(request, "You cannot delete your own Super User account.")
            elif user_to_delete.role in ['ADMIN', 'STAFF', 'EMPLOYEE', 'CUSTOMER']:
                username = user_to_delete.username
                role = user_to_delete.get_role_display()
                user_to_delete.delete()
                messages.warning(request, f"{role} '{username}' has been permanently deleted.")
            else:
                messages.error(request, "Only Admin, Staff, Employee, and Customer accounts can be deleted.")
            return redirect('superuser_dashboard')
        elif action == 'close_project':
            project_id = request.POST.get('project_id')
            project = get_object_or_404(SolarInstallationProject, id=project_id)
            project.status = 'COMPLETED'
            project.save()
            messages.success(request, f"Solar project '{project.title}' has been successfully completed and closed!")
            return redirect('superuser_dashboard')
        elif action == 'resolve_complaint':
            complaint_id = request.POST.get('complaint_id')
            complaint = get_object_or_404(Complaint, id=complaint_id)
            complaint.status = 'RESOLVED'
            complaint.resolved_at = timezone.now()
            complaint.save()
            messages.success(request, f"Complaint by customer '{complaint.customer.username}' has been marked as resolved!")
            return redirect('superuser_dashboard')

        elif action == 'mark_attendance':
            date_str = request.POST.get('attendance_date')
            try:
                att_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                att_date = datetime.today().date()
                date_str = att_date.strftime('%Y-%m-%d')
            
            for worker in workers:
                status_key = f"status_{worker.id}"
                notes_key = f"notes_{worker.id}"
                status_val = request.POST.get(status_key)
                notes_val = request.POST.get(notes_key, '')
                if status_val:
                    Attendance.objects.update_or_create(
                        user=worker,
                        date=att_date,
                        defaults={'status': status_val, 'notes': notes_val}
                    )
            messages.success(request, f"Attendance successfully marked for {att_date.strftime('%b %d, %Y')}!")
            return redirect(f"{reverse('superuser_dashboard')}?date={date_str}")

    # Global company financial and installation metrics
    total_revenue = SolarInstallationProject.objects.exclude(status='COMPLETED').aggregate(Sum('total_value'))['total_value__sum'] or Decimal('0.00')
    total_received = SolarInstallationProject.objects.exclude(status='COMPLETED').aggregate(Sum('advances_paid'))['advances_paid__sum'] or Decimal('0.00')
    remaining_balance = total_revenue - total_received
    completed_project_value = SolarInstallationProject.objects.filter(status='COMPLETED').aggregate(Sum('total_value'))['total_value__sum'] or Decimal('0.00')

    total_projects = SolarInstallationProject.objects.count()
    completed_projects = SolarInstallationProject.objects.filter(status='COMPLETED').count()
    active_projects = SolarInstallationProject.objects.exclude(status__in=['COMPLETED', 'PENDING_APPROVAL']).count()
    pending_projects = SolarInstallationProject.objects.filter(status='PENDING_APPROVAL').count()

    # Blank forms for creation
    admin_form = AdminCreationForm()
    staff_form = StaffCreationForm()
    employee_form = EmployeeCreationForm()
    customer_form = AdminCustomerCreationForm()
    project_form = ProjectForm()

    # Status distribution counts for Chart.js
    statuses = dict(SolarInstallationProject.STATUS_CHOICES)
    status_counts = []
    status_labels = []
    for key, name in statuses.items():
        count = SolarInstallationProject.objects.filter(status=key).count()
        status_counts.append(count)
        status_labels.append(name)

    # Simulated audit log
    audit_logs = [
        {"timestamp": "Just Now", "event": f"Super User {request.user.username} viewed executive reports.", "status": "info"},
        {"timestamp": "2 Hours Ago", "event": "System automatically compiled end-of-day solar revenue.", "status": "success"},
        {"timestamp": "Yesterday", "event": "Database connection verified and backup stored.", "status": "success"},
    ]

    # Load unapproved user accounts
    pending_users = CustomUser.objects.filter(role__in=['CUSTOMER', 'STAFF', 'EMPLOYEE'], is_approved=False).order_by('-date_joined')
    pending_approvals_count = pending_users.count()

    pending_complaints = Complaint.objects.filter(status='PENDING').order_by('-created_at')
    resolved_complaints = Complaint.objects.filter(status='RESOLVED').order_by('-resolved_at')
    pending_complaints_count = pending_complaints.count()
    # Project Expenses
    expenses = ProjectExpense.objects.all().order_by('-date', '-id')
    expense_projects = SolarInstallationProject.objects.all().order_by('-id')
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0.00

    context = {
        'total_revenue': total_revenue,
        'total_received': total_received,
        'remaining_balance': remaining_balance,
        'completed_project_value': completed_project_value,
        'total_projects': total_projects,
        'completed_projects': completed_projects,
        'active_projects': active_projects,
        'pending_projects': pending_projects,
        
        # Registry lists with edit forms
        'admins_list': admins_list,
        'staff_data_list': staff_data_list,
        'employees_data_list': employees_data_list,
        'customer_data_list': customer_data_list,
        'project_data_list': project_data_list,
        'pending_customers': pending_users,
        'pending_approvals_count': pending_approvals_count,
        
        # Blank forms for creation
        'admin_form': admin_form,
        'staff_form': staff_form,
        'employee_form': employee_form,
        'customer_form': customer_form,
        'project_form': project_form,
        
        'staff_count': staff_members.count(),
        'customer_count': len(customer_data_list),
        'status_counts_json': status_counts,
        'status_labels_json': status_labels,
        'audit_logs': audit_logs,
        
        # Attendance params
        'attendance_data': attendance_data,
        'attendance_date_str': attendance_date_str,
        'attendance_stats': attendance_stats,
        
        # Complaints params
        'pending_complaints': pending_complaints,
        'resolved_complaints': resolved_complaints,
        'pending_complaints_count': pending_complaints_count,

        # Worker search
        'worker_search': worker_search,
        'current_month_name': timezone.now().strftime('%B'),
        
        # Project Expenses
        'expenses': expenses,
        'expense_projects': expense_projects,
        'total_expenses': total_expenses,
    }
    return render(request, 'core/superuser_dashboard.html', context)


@login_required
def admin_approve_customer(request, user_id):
    if request.user.role not in ['ADMIN', 'SUPERUSER'] and not request.user.is_superuser:
        return HttpResponseForbidden()
    
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_approved = True
    user.is_active = True
    user.save()
    messages.success(request, f"Account '{user.username}' has been approved and activated.")
    if request.user.role == 'SUPERUSER' or request.user.is_superuser:
        return redirect('superuser_dashboard')
    return redirect('admin_dashboard')


@login_required
def admin_revoke_customer(request, user_id):
    if request.user.role not in ['ADMIN', 'SUPERUSER'] and not request.user.is_superuser:
        return HttpResponseForbidden()

    user = get_object_or_404(CustomUser, id=user_id)
    user.is_approved = False
    user.is_active = False
    user.save()
    messages.warning(request, f"Account '{user.username}' access has been revoked.")
    if request.user.role == 'SUPERUSER' or request.user.is_superuser:
        return redirect('superuser_dashboard')
    return redirect('admin_dashboard')


@login_required
def export_attendance_csv(request):
    if request.user.role not in ['ADMIN', 'SUPERUSER'] and not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: Admins Only")
    
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_report_{datetime.now().strftime("%Y-%m-%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Username', 'Full Name', 'Role', 'Employee ID', 'Status', 'Notes'])
    
    records = Attendance.objects.all().order_by('-date', 'user__role', 'user__username')
    for record in records:
        writer.writerow([
            record.date.strftime('%Y-%m-%d'),
            record.user.username,
            record.user.get_full_name() or record.user.username,
            record.user.get_role_display(),
            record.user.employee_id or 'N/A',
            record.get_status_display(),
            record.notes or ''
        ])
        
    return response


@login_required
def export_projects_csv(request):
    if request.user.role not in ['ADMIN', 'SUPERUSER'] and not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: Admins Only")
    
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="projects_report_{datetime.now().strftime("%Y-%m-%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Project Title', 'Customer Username', 'Customer Name', 'Staff In-charge', 'Status', 'Advances Paid (INR)', 'Total Value (INR)', 'Remaining Balance (INR)', 'Start Date', 'End Date', 'Laborers Count', 'Crew Details'])
    
    projects = SolarInstallationProject.objects.all().order_by('-start_date')
    for project in projects:
        writer.writerow([
            project.title,
            project.customer.username,
            project.customer.get_full_name() or project.customer.username,
            project.staff_incharge.get_full_name() if project.staff_incharge else 'Unassigned',
            project.get_status_display(),
            project.advances_paid,
            project.total_value,
            project.remaining_balance,
            project.start_date.strftime('%Y-%m-%d') if project.start_date else 'TBD',
            project.end_date.strftime('%Y-%m-%d') if project.end_date else 'TBD',
            project.laborers_count,
            project.crew_details or ''
        ])
        
    return response


@login_required
def export_salaries_csv(request):
    if request.user.role not in ['ADMIN', 'SUPERUSER'] and not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: Admins Only")
    
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="salary_payroll_report_{datetime.now().strftime("%Y-%m-%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Username', 'Full Name', 'Role', 'Unique Employee ID', 'Base Monthly Salary (INR)', f'Current Month ({timezone.now().strftime("%B")}) Attendance Rating (%)', 'Current Month Calculated Payout (INR)', 'Overall Attendance Rating (%)', 'Overall Calculated Payout (INR)'])
    
    workers = CustomUser.objects.filter(role__in=['STAFF', 'EMPLOYEE']).order_by('role', 'username')
    now = timezone.now()
    
    for worker in workers:
        # Overall rating
        total_days = Attendance.objects.filter(user=worker).count()
        present_days = Attendance.objects.filter(user=worker, status='PRESENT').count()
        rating_pct = (present_days / total_days * 100) if total_days > 0 else 100.0
        calculated_salary_overall = Decimal(float(worker.salary or 0.00) * (rating_pct / 100.0))
        
        # Monthly rating
        total_days_monthly = Attendance.objects.filter(user=worker, date__year=now.year, date__month=now.month).count()
        present_days_monthly = Attendance.objects.filter(user=worker, status='PRESENT', date__year=now.year, date__month=now.month).count()
        rating_pct_monthly = (present_days_monthly / total_days_monthly * 100) if total_days_monthly > 0 else 100.0
        calculated_salary_monthly = Decimal(float(worker.salary or 0.00) * (rating_pct_monthly / 100.0))
        
        writer.writerow([
            worker.username,
            worker.get_full_name() or worker.username,
            worker.get_role_display(),
            worker.employee_id or 'N/A',
            worker.salary,
            f"{rating_pct_monthly:.1f}%",
            f"{calculated_salary_monthly:.2f}",
            f"{rating_pct:.1f}%",
            f"{calculated_salary_overall:.2f}"
        ])
        
    return response



@login_required
def create_notice_view(request):
    if request.user.role not in ['ADMIN', 'SUPERUSER'] and not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: Admins/Super Users Only")

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        
        if title and content:
            Notice.objects.create(
                author=request.user,
                title=title,
                content=content
            )
            messages.success(request, "Announcement notice published successfully!")
        else:
            messages.error(request, "Failed to publish notice. Subject and content cannot be empty.")
            
    next_url = request.META.get('HTTP_REFERER', 'dashboard')
    return redirect(next_url)


@login_required
def delete_notice_view(request, notice_id):
    if request.user.role not in ['ADMIN', 'SUPERUSER'] and not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: Admins/Super Users Only")
        
    notice = get_object_or_404(Notice, id=notice_id)
    notice.delete()
    messages.success(request, "Notice deleted successfully!")
    
    next_url = request.META.get('HTTP_REFERER', 'dashboard')
    return redirect(next_url)


@login_required
def add_quotation_view(request):
    if request.user.role not in ['ADMIN', 'SUPERUSER'] and not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: Admins/Super Users Only")
        
    if request.method == 'POST':
        form = QuotationForm(request.POST)
        if form.is_valid():
            quotation = form.save(commit=False)
            quotation.created_by = request.user
            quotation.save()
            messages.success(request, "Solar quotation generated successfully!")
        else:
            errors_str = " ".join([f"{k}: {v[0]}" for k, v in form.errors.items()])
            messages.error(request, f"Failed to generate quotation: {errors_str}")
            
    next_url = request.META.get('HTTP_REFERER', 'dashboard')
    return redirect(next_url)


@login_required
def edit_quotation_view(request, quote_id):
    if request.user.role not in ['ADMIN', 'SUPERUSER'] and not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: Admins/Super Users Only")
        
    quotation = get_object_or_404(Quotation, id=quote_id)
    if request.method == 'POST':
        form = QuotationForm(request.POST, instance=quotation)
        if form.is_valid():
            form.save()
            messages.success(request, "Quotation updated successfully!")
        else:
            errors_str = " ".join([f"{k}: {v[0]}" for k, v in form.errors.items()])
            messages.error(request, f"Failed to update quotation: {errors_str}")
            
    next_url = request.META.get('HTTP_REFERER', 'dashboard')
    return redirect(next_url)


@login_required
def delete_quotation_view(request, quote_id):
    if request.user.role not in ['ADMIN', 'SUPERUSER'] and not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: Admins/Super Users Only")
        
    quotation = get_object_or_404(Quotation, id=quote_id)
    quotation.delete()
    messages.success(request, "Quotation deleted successfully!")
    
    next_url = request.META.get('HTTP_REFERER', 'dashboard')
    return redirect(next_url)


@login_required
def view_quotation_proposal_view(request, quote_id):
    quotation = get_object_or_404(Quotation, id=quote_id)
    
    # Access checks:
    # 1. Admins / Superusers can view any quotation.
    # 2. Customers can view their own quotations if the status is NOT DRAFT.
    is_admin = request.user.role in ['ADMIN', 'SUPERUSER'] or request.user.is_superuser
    is_owner = quotation.customer == request.user and quotation.status != 'DRAFT'
    
    if not (is_admin or is_owner):
        return HttpResponseForbidden("Access Denied: You do not have permission to view this quotation.")
        
    context = {
        'quotation': quotation,
        'material_items': [item.strip() for item in quotation.material_breakdown.split('\n') if item.strip()] if quotation.material_breakdown else [],
    }
    return render(request, 'core/quotation_proposal_print.html', context)


@login_required
def add_expense_view(request):
    if request.user.role not in ['ADMIN', 'SUPERUSER', 'STAFF'] and not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: Unauthorized to manage project expenses.")
        
    if request.method == 'POST':
        form = ProjectExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            # Double check permission for staff
            if request.user.role == 'STAFF' and expense.project.staff_incharge != request.user:
                return HttpResponseForbidden("Access Denied: You cannot add expenses to a project you are not in charge of.")
            expense.save()
            messages.success(request, f"Project expense '{expense.title}' of ₹{expense.amount} added successfully!")
        else:
            errors_str = " ".join([f"{k}: {v[0]}" for k, v in form.errors.items()])
            messages.error(request, f"Failed to add expense: {errors_str}")
            
    next_url = request.META.get('HTTP_REFERER', 'dashboard')
    return redirect(next_url)


@login_required
def edit_expense_view(request, expense_id):
    if request.user.role not in ['ADMIN', 'SUPERUSER', 'STAFF'] and not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: Unauthorized to manage project expenses.")
        
    expense = get_object_or_404(ProjectExpense, id=expense_id)
    # Double check permission for staff
    if request.user.role == 'STAFF' and expense.project.staff_incharge != request.user:
        return HttpResponseForbidden("Access Denied: You cannot manage expenses for a project you are not in charge of.")
        
    if request.method == 'POST':
        form = ProjectExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Project expense '{expense.title}' updated successfully!")
        else:
            errors_str = " ".join([f"{k}: {v[0]}" for k, v in form.errors.items()])
            messages.error(request, f"Failed to update expense: {errors_str}")
            
    next_url = request.META.get('HTTP_REFERER', 'dashboard')
    return redirect(next_url)


@login_required
def delete_expense_view(request, expense_id):
    if request.user.role not in ['ADMIN', 'SUPERUSER', 'STAFF'] and not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: Unauthorized to manage project expenses.")
        
    expense = get_object_or_404(ProjectExpense, id=expense_id)
    # Double check permission for staff
    if request.user.role == 'STAFF' and expense.project.staff_incharge != request.user:
        return HttpResponseForbidden("Access Denied: You cannot delete expenses for a project you are not in charge of.")
        
    expense.delete()
    messages.success(request, "Project expense deleted successfully!")
    
    next_url = request.META.get('HTTP_REFERER', 'dashboard')
    return redirect(next_url)



