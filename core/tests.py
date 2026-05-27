from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import SolarInstallationProject, Attendance, Complaint

User = get_user_model()

class SuperUserDashboardTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create Super User
        self.superuser = User.objects.create_superuser(
            username="superuser",
            email="superuser@solar.com",
            password="solar123",
            role="SUPERUSER",
            is_approved=True,
            first_name="Root",
            last_name="Admin"
        )
        
        # Create a helper Admin, Staff, Customer, and Project for testing edits
        self.test_admin = User.objects.create_user(
            username="testadmin",
            email="admin@test.com",
            password="adminpassword",
            role="ADMIN",
            is_approved=True
        )
        
        self.test_staff = User.objects.create_user(
            username="teststaff",
            email="staff@test.com",
            password="staffpassword",
            role="STAFF",
            is_approved=True,
            employee_id="STF-1234"
        )
        
        self.test_customer = User.objects.create_user(
            username="testcustomer",
            email="customer@test.com",
            password="customerpassword",
            role="CUSTOMER",
            is_approved=True
        )
        
        self.test_employee = User.objects.create_user(
            username="testemployee",
            email="employee@test.com",
            password="employeepassword",
            role="EMPLOYEE",
            is_approved=True,
            employee_id="EMP-1234"
        )
        
        self.test_project = SolarInstallationProject.objects.create(
            customer=self.test_customer,
            staff_incharge=self.test_staff,
            title="Initial Test Solar Setup",
            status="SITE_SURVEY",
            total_value=120000.00,
            advances_paid=40000.00,
            start_date="2026-05-01",
            end_date="2026-05-30",
            laborers_count=3,
            crew_details="testemployee (Lead Technician - EMP-1234), Assistant"
        )

    def test_superuser_dashboard_access_denied_for_staff(self):
        """Verify that staff members cannot access the superuser dashboard."""
        self.client.login(username="teststaff", password="staffpassword")
        response = self.client.get(reverse('superuser_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_superuser_dashboard_access_granted_for_superuser(self):
        """Verify that the superuser can access their dashboard successfully."""
        self.client.login(username="superuser", password="solar123")
        response = self.client.get(reverse('superuser_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/superuser_dashboard.html')

    def test_create_admin_account(self):
        """Verify that the superuser can provision a new custom Admin account."""
        self.client.login(username="superuser", password="solar123")
        response = self.client.post(reverse('superuser_dashboard'), {
            'action': 'create_admin',
            'username': 'newadmin',
            'email': 'newadmin@solar.com',
            'first_name': 'New',
            'last_name': 'AdminUser',
            'phone_number': '+918888888888',
            'whatsapp_number': '918888888888',
            'bio': 'On-site regional admin.',
            'password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 302)  # Redirects on success
        
        # Verify user is created in database with role ADMIN
        new_admin = User.objects.get(username='newadmin')
        self.assertEqual(new_admin.role, 'ADMIN')
        self.assertTrue(new_admin.is_approved)
        self.assertEqual(new_admin.email, 'newadmin@solar.com')

    def test_edit_admin_profile(self):
        """Verify that the superuser can edit an Admin's profile parameters directly."""
        self.client.login(username="superuser", password="solar123")
        response = self.client.post(reverse('superuser_dashboard'), {
            'action': 'edit_admin',
            'admin_id': self.test_admin.id,
            'email': 'updatedadmin@test.com',
            'first_name': 'Updated',
            'last_name': 'AdminName',
            'phone_number': '+911111111111',
            'whatsapp_number': '911111111111',
            'bio': 'Updated regional bio details.'
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify database fields updated
        self.test_admin.refresh_from_db()
        self.assertEqual(self.test_admin.email, 'updatedadmin@test.com')
        self.assertEqual(self.test_admin.first_name, 'Updated')
        self.assertEqual(self.test_admin.bio, 'Updated regional bio details.')

    def test_reset_user_password(self):
        """Verify that the superuser can reset the password for any user type."""
        self.client.login(username="superuser", password="solar123")
        
        # Reset Admin's password
        response = self.client.post(reverse('superuser_dashboard'), {
            'action': 'reset_password',
            'user_id': self.test_admin.id,
            'new_password': 'supernewadminpassword123'
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify the new password works for login
        login_success = self.client.login(username="testadmin", password="supernewadminpassword123")
        self.assertTrue(login_success)

    def test_create_staff_account(self):
        """Verify that the superuser can onboard a new Staff worker directly."""
        self.client.login(username="superuser", password="solar123")
        response = self.client.post(reverse('superuser_dashboard'), {
            'action': 'create_staff',
            'username': 'newstaff',
            'email': 'newstaff@solar.com',
            'first_name': 'Worker',
            'last_name': 'One',
            'phone_number': '+917777777777',
            'whatsapp_number': '917777777777',
            'bio': 'Solar panel layout technician.',
            'password': 'staffpassword123'
        })
        self.assertEqual(response.status_code, 302)
        
        new_staff = User.objects.get(username='newstaff')
        self.assertEqual(new_staff.role, 'STAFF')
        self.assertTrue(new_staff.is_approved)
        # Unique ID generated automatically
        self.assertTrue(new_staff.employee_id.startswith('STF-'))

    def test_edit_staff_profile(self):
        """Verify that the superuser can edit Staff profile parameters directly."""
        self.client.login(username="superuser", password="solar123")
        response = self.client.post(reverse('superuser_dashboard'), {
            'action': 'edit_staff',
            'staff_id': self.test_staff.id,
            'email': 'updatedstaff@test.com',
            'first_name': 'Updated',
            'last_name': 'StaffName',
            'phone_number': '+912222222222',
            'whatsapp_number': '912222222222',
            'employee_id': 'STF-8888',
            'bio': 'Certified inverter engineer.'
        })
        self.assertEqual(response.status_code, 302)
        
        self.test_staff.refresh_from_db()
        self.assertEqual(self.test_staff.email, 'updatedstaff@test.com')
        self.assertEqual(self.test_staff.employee_id, 'STF-8888')
        self.assertEqual(self.test_staff.bio, 'Certified inverter engineer.')

    def test_create_employee_account(self):
        """Verify that the superuser can onboard a new Employee worker directly."""
        self.client.login(username="superuser", password="solar123")
        response = self.client.post(reverse('superuser_dashboard'), {
            'action': 'create_employee',
            'username': 'newemployee',
            'email': 'newemployee@solar.com',
            'first_name': 'Technician',
            'last_name': 'Two',
            'phone_number': '+914444444444',
            'whatsapp_number': '914444444444',
            'bio': 'Solar panel roofer.',
            'password': 'employeepassword123'
        })
        self.assertEqual(response.status_code, 302)
        
        new_emp = User.objects.get(username='newemployee')
        self.assertEqual(new_emp.role, 'EMPLOYEE')
        self.assertTrue(new_emp.is_approved)
        # Unique ID generated automatically
        self.assertTrue(new_emp.employee_id.startswith('EMP-'))

    def test_edit_employee_profile(self):
        """Verify that the superuser can edit Employee profile parameters directly."""
        self.client.login(username="superuser", password="solar123")
        response = self.client.post(reverse('superuser_dashboard'), {
            'action': 'edit_employee',
            'worker_id': self.test_employee.id,
            'email': 'updatedemp@test.com',
            'first_name': 'Updated',
            'last_name': 'EmpName',
            'phone_number': '+914444444444',
            'whatsapp_number': '914444444444',
            'employee_id': 'EMP-9999',
            'bio': 'Inverter wiring expert.'
        })
        self.assertEqual(response.status_code, 302)
        
        self.test_employee.refresh_from_db()
        self.assertEqual(self.test_employee.email, 'updatedemp@test.com')
        self.assertEqual(self.test_employee.employee_id, 'EMP-9999')
        self.assertEqual(self.test_employee.bio, 'Inverter wiring expert.')

    def test_create_customer_account(self):
        """Verify that the superuser can register a Customer account directly."""
        self.client.login(username="superuser", password="solar123")
        response = self.client.post(reverse('superuser_dashboard'), {
            'action': 'create_customer',
            'username': 'newcustomer',
            'email': 'newcustomer@solar.com',
            'first_name': 'Client',
            'last_name': 'Direct',
            'phone_number': '+916666666666',
            'whatsapp_number': '916666666666',
            'password': 'customerpassword123'
        })
        self.assertEqual(response.status_code, 302)
        
        new_cust = User.objects.get(username='newcustomer')
        self.assertEqual(new_cust.role, 'CUSTOMER')
        self.assertTrue(new_cust.is_approved)

    def test_edit_customer_profile(self):
        """Verify that the superuser can edit Customer profile parameters directly."""
        self.client.login(username="superuser", password="solar123")
        response = self.client.post(reverse('superuser_dashboard'), {
            'action': 'edit_customer',
            'customer_id': self.test_customer.id,
            'email': 'updatedcustomer@test.com',
            'first_name': 'Updated',
            'last_name': 'CustomerName',
            'phone_number': '+913333333333',
            'whatsapp_number': '913333333333'
        })
        self.assertEqual(response.status_code, 302)
        
        self.test_customer.refresh_from_db()
        self.assertEqual(self.test_customer.email, 'updatedcustomer@test.com')
        self.assertEqual(self.test_customer.phone_number, '+913333333333')

    def test_approve_and_revoke_customer_access(self):
        """Verify that the superuser can approve and deactivate Customer login access."""
        self.client.login(username="superuser", password="solar123")
        
        # Revoke customer access
        response = self.client.get(reverse('admin_revoke_customer', args=[self.test_customer.id]))
        self.assertEqual(response.status_code, 302)
        self.test_customer.refresh_from_db()
        self.assertFalse(self.test_customer.is_approved)
        self.assertFalse(self.test_customer.is_active)
        
        # Approve customer access
        response = self.client.get(reverse('admin_approve_customer', args=[self.test_customer.id]))
        self.assertEqual(response.status_code, 302)
        self.test_customer.refresh_from_db()
        self.assertTrue(self.test_customer.is_approved)
        self.assertTrue(self.test_customer.is_active)

    def test_create_and_edit_project_milestone(self):
        """Verify that the superuser can create a project and update its milestone pipeline details."""
        self.client.login(username="superuser", password="solar123")
        
        # Create Project
        response = self.client.post(reverse('superuser_dashboard'), {
            'action': 'create_project',
            'customer': self.test_customer.id,
            'staff_incharge': self.test_staff.id,
            'title': 'New Residential Solar Array',
            'status': 'ENGINEERING',
            'total_value': 250000.00,
            'advances_paid': 50000.00,
            'start_date': '2026-06-01',
            'end_date': '2026-06-30',
            'laborers_count': 4,
            'crew_details': 'Chris, David'
        })
        self.assertEqual(response.status_code, 302)
        
        new_proj = SolarInstallationProject.objects.get(title='New Residential Solar Array')
        self.assertEqual(new_proj.status, 'ENGINEERING')
        self.assertEqual(new_proj.customer, self.test_customer)
        
        # Edit Project Milestone Stage to INSTALLATION
        response = self.client.post(reverse('superuser_dashboard'), {
            'action': 'edit_project',
            'project_id': self.test_project.id,
            'customer': self.test_customer.id,
            'staff_incharge': self.test_staff.id,
            'title': 'Initial Test Solar Setup - Phase 2',
            'status': 'INSTALLATION',
            'total_value': 120000.00,
            'advances_paid': 90000.00,
            'start_date': '2026-05-01',
            'end_date': '2026-06-15',
            'laborers_count': 6,
            'crew_details': 'Alice, Bob, Kevin'
        })
        self.assertEqual(response.status_code, 302)
        
        self.test_project.refresh_from_db()
        self.assertEqual(self.test_project.status, 'INSTALLATION')
        self.assertEqual(self.test_project.title, 'Initial Test Solar Setup - Phase 2')
        self.assertEqual(self.test_project.laborers_count, 6)

    def test_employee_dashboard_access_granted(self):
        """Verify that employees can access their self-service dashboard."""
        self.client.login(username="testemployee", password="employeepassword")
        response = self.client.get(reverse('employee_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/employee_dashboard.html')

    def test_daily_attendance_marking_log(self):
        """Verify that Admins/Super Users can mark and save daily check-in logs."""
        self.client.login(username="superuser", password="solar123")
        
        # Post daily check-ins
        response = self.client.post(reverse('superuser_dashboard'), {
            'action': 'mark_attendance',
            'attendance_date': '2026-05-24',
            f'status_{self.test_staff.id}': 'PRESENT',
            f'notes_{self.test_staff.id}': 'Arrived early on-site',
            f'status_{self.test_employee.id}': 'LEAVE',
            f'notes_{self.test_employee.id}': 'Approved sick leave'
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify attendance record created in database
        staff_log = Attendance.objects.get(user=self.test_staff, date='2026-05-24')
        self.assertEqual(staff_log.status, 'PRESENT')
        self.assertEqual(staff_log.notes, 'Arrived early on-site')
        
        emp_log = Attendance.objects.get(user=self.test_employee, date='2026-05-24')
        self.assertEqual(emp_log.status, 'LEAVE')
        self.assertEqual(emp_log.notes, 'Approved sick leave')

    def test_customer_can_raise_complaint(self):
        """Verify that a customer can successfully submit a support complaint."""
        self.client.login(username="testcustomer", password="customerpassword")
        response = self.client.post(reverse('customer_dashboard'), {
            'action': 'raise_complaint',
            'subject': 'Solar inverter error code 30',
            'description': 'The inverter is displaying red light with warning code 30.'
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify it exists in database
        complaint = Complaint.objects.get(customer=self.test_customer)
        self.assertEqual(complaint.subject, 'Solar inverter error code 30')
        self.assertEqual(complaint.status, 'PENDING')

    def test_complaints_restricted_visibility(self):
        """Verify that only Admins and Super Users can view complaints."""
        complaint = Complaint.objects.create(
            customer=self.test_customer,
            subject='Panel physical crack',
            description='One panel has a physical crack.'
        )
        
        # Super User can view
        self.client.login(username="superuser", password="solar123")
        response = self.client.get(reverse('superuser_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Panel physical crack')
        
        # Admin can view
        self.client.login(username="testadmin", password="adminpassword")
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Panel physical crack')
        
        # Staff cannot view superuser_dashboard or admin_dashboard
        self.client.login(username="teststaff", password="staffpassword")
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_resolve_complaint_by_admin(self):
        """Verify that an admin can resolve a complaint."""
        complaint = Complaint.objects.create(
            customer=self.test_customer,
            subject='Loose wiring',
            description='Inverter switch is loose.'
        )
        self.assertEqual(complaint.status, 'PENDING')
        
        self.client.login(username="testadmin", password="adminpassword")
        response = self.client.post(reverse('admin_dashboard'), {
            'action': 'resolve_complaint',
            'complaint_id': complaint.id
        })
        self.assertEqual(response.status_code, 302)
        
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, 'RESOLVED')
        self.assertIsNotNone(complaint.resolved_at)

    def test_completed_project_value_metric(self):
        """Verify that completed projects sum up to the Closed Project Value metric."""
        SolarInstallationProject.objects.create(
            customer=self.test_customer,
            staff_incharge=self.test_staff,
            title="Completed Solar Setup",
            status="COMPLETED",
            total_value=150000.00,
            advances_paid=150000.00,
            start_date="2026-05-01",
            end_date="2026-05-20",
            laborers_count=2,
            crew_details="testemployee"
        )
        
        self.client.login(username="superuser", password="solar123")
        response = self.client.get(reverse('superuser_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Closed Project Value")
        self.assertContains(response, "150000.00")
