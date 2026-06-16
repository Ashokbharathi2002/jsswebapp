from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal
from core.models import SolarInstallationProject, Attendance, Complaint, LoginLog, Inspection, Notification

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
        proj = SolarInstallationProject.objects.create(
            customer=self.test_customer,
            staff_incharge=self.test_staff,
            title="Completed Solar Setup",
            status="INSTALLATION",
            total_value=150000.00,
            advances_paid=150000.00,
            start_date="2026-05-01",
            end_date="2026-05-20",
            laborers_count=2,
            crew_details="testemployee"
        )
        proj.inverter.brand = "Sungrow"
        proj.inverter.model = "SG5.0RS"
        proj.inverter.serial_number = "SN12345678"
        proj.inverter.capacity = Decimal("5.00")
        proj.inverter.save()
        proj.status = "COMPLETED"
        proj.save()
        
        self.client.login(username="superuser", password="solar123")
        response = self.client.get(reverse('superuser_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Closed Project Value")
        self.assertContains(response, "150000.00")

    def test_self_service_password_change_success(self):
        """Verify any logged-in user can change their password successfully."""
        self.client.login(username="testcustomer", password="customerpassword")
        response = self.client.post(reverse('change_password'), {
            'current_password': 'customerpassword',
            'new_password': 'newpassword123',
            'confirm_new_password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify the password was actually updated and the user can log in with it
        self.client.logout()
        login_success = self.client.login(username="testcustomer", password="newpassword123")
        self.assertTrue(login_success)

    def test_self_service_password_change_incorrect_current(self):
        """Verify password change fails if the current password is wrong."""
        self.client.login(username="testcustomer", password="customerpassword")
        response = self.client.post(reverse('change_password'), {
            'current_password': 'wrongcurrentpassword',
            'new_password': 'newpassword123',
            'confirm_new_password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify password remains unchanged
        self.client.logout()
        login_fails = self.client.login(username="testcustomer", password="newpassword123")
        self.assertFalse(login_fails)
        login_works = self.client.login(username="testcustomer", password="customerpassword")
        self.assertTrue(login_works)

    def test_admin_force_reset_staff_password(self):
        """Verify an administrator can force-reset a staff lead's password from the admin dashboard."""
        self.client.login(username="testadmin", password="adminpassword")
        response = self.client.post(reverse('admin_dashboard'), {
            'action': 'reset_password',
            'user_id': self.test_staff.id,
            'new_password': 'newstaffpassword123'
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify the staff password is updated and they can log in
        self.client.logout()
        login_success = self.client.login(username="teststaff", password="newstaffpassword123")
        self.assertTrue(login_success)

    def test_superuser_delete_customer(self):
        """Verify that a superuser can permanently delete a Customer (client) account."""
        self.client.login(username="superuser", password="solar123")
        
        # Verify customer exists before deletion
        self.assertTrue(User.objects.filter(id=self.test_customer.id).exists())
        
        # Delete customer via dashboard action
        response = self.client.post(reverse('superuser_dashboard'), {
            'action': 'delete_user',
            'user_id': self.test_customer.id
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify customer has been permanently deleted from database
        self.assertFalse(User.objects.filter(id=self.test_customer.id).exists())


class NoticeTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Get active user model
        self.user = User.objects.create_user(
            username="regularuser",
            email="regularuser@test.com",
            password="userpassword",
            role="CUSTOMER",
            is_approved=True
        )
        self.admin = User.objects.create_user(
            username="adminuser",
            email="adminuser@test.com",
            password="adminpassword",
            role="ADMIN",
            is_approved=True
        )

    def test_create_and_delete_notice_by_admin(self):
        """Verify noticeboard announcements can be created and deleted by admins."""
        self.client.login(username="adminuser", password="adminpassword")
        response = self.client.post(reverse('create_notice'), {
            'title': 'System Maintenance Announcement',
            'content': 'There will be a maintenance window tonight.'
        })
        self.assertEqual(response.status_code, 302)
        from core.models import Notice
        notice = Notice.objects.filter(author=self.admin).first()
        self.assertIsNotNone(notice)
        self.assertEqual(notice.title, 'System Maintenance Announcement')

        # Test delete notice
        delete_response = self.client.get(reverse('delete_notice', args=[notice.id]))
        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(Notice.objects.filter(id=notice.id).exists())

    def test_create_notice_forbidden_for_regular_user(self):
        """Verify that regular users cannot publish noticeboard announcements."""
        self.client.login(username="regularuser", password="userpassword")
        response = self.client.post(reverse('create_notice'), {
            'title': 'Hack attempt',
            'content': 'Should fail'
        })
        self.assertEqual(response.status_code, 403)


class QuotationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username="adminuser",
            email="admin@test.com",
            password="adminpassword",
            role="ADMIN",
            is_approved=True
        )
        self.customer_one = User.objects.create_user(
            username="customer1",
            email="cust1@test.com",
            password="custpassword",
            role="CUSTOMER",
            is_approved=True
        )
        self.customer_two = User.objects.create_user(
            username="customer2",
            email="cust2@test.com",
            password="custpassword",
            role="CUSTOMER",
            is_approved=True
        )
        self.staff = User.objects.create_user(
            username="staffuser",
            email="staff@test.com",
            password="staffpassword",
            role="STAFF",
            is_approved=True
        )

    def test_admin_generate_quotation_and_auto_total_calculation(self):
        """Verify that an admin can create a quotation, and the total price defaults to the sum of costs."""
        self.client.login(username="adminuser", password="adminpassword")
        response = self.client.post(reverse('add_quotation'), {
            'customer': self.customer_one.id,
            'title': '3kW Smart Solar Array',
            'solar_capacity_kw': '3.20',
            'material_breakdown': '8x 400W Panels\nInverter',
            'material_cost': '100000.00',
            'labor_cost': '20000.00',
            'tax_cost': '5000.00',
            'total_price': '0.00',  # Let it auto-calculate
            'status': 'DRAFT'
        })
        self.assertEqual(response.status_code, 302)
        from core.models import Quotation
        quote = Quotation.objects.filter(customer=self.customer_one).first()
        self.assertIsNotNone(quote)
        self.assertEqual(quote.title, '3kW Smart Solar Array')
        # Check auto calculation of total price
        self.assertEqual(quote.total_price, Decimal('125000.00'))

    def test_add_quotation_requires_customer_or_lead_name(self):
        """Verify form validation errors if both registered customer and lead name are empty."""
        self.client.login(username="adminuser", password="adminpassword")
        # Submit empty customer and empty lead name
        response = self.client.post(reverse('add_quotation'), {
            'title': 'Invalid Proposal',
            'solar_capacity_kw': '5.00',
            'material_cost': '0.00',
            'labor_cost': '0.00',
            'tax_cost': '0.00',
            'status': 'DRAFT'
        })
        self.assertEqual(response.status_code, 302)
        # Verify no Quotation was created
        from core.models import Quotation
        self.assertEqual(Quotation.objects.count(), 0)

    def test_client_cannot_access_quotation_actions(self):
        """Verify that clients/customers cannot create, edit, or delete quotations."""
        self.client.login(username="customer1", password="custpassword")
        
        # Test add
        add_resp = self.client.post(reverse('add_quotation'), {'title': 'Hack'})
        self.assertEqual(add_resp.status_code, 403)
        
        # Create a mock quote to test edit/delete
        from core.models import Quotation
        quote = Quotation.objects.create(
            created_by=self.admin,
            customer=self.customer_one,
            title="Safe Quote",
            solar_capacity_kw=5.00,
            material_cost=100.00,
            status="DRAFT"
        )
        
        # Test edit
        edit_resp = self.client.post(reverse('edit_quotation', args=[quote.id]), {'title': 'Hacked Title'})
        self.assertEqual(edit_resp.status_code, 403)
        
        # Test delete
        delete_resp = self.client.post(reverse('delete_quotation', args=[quote.id]))
        self.assertEqual(delete_resp.status_code, 403)

    def test_client_quotation_visibility_restrictions(self):
        """Verify that customers can only view their own non-draft quotations."""
        from core.models import Quotation
        # 1. Draft quote for customer_one (Customer 1 should NOT be able to view)
        draft_quote = Quotation.objects.create(
            created_by=self.admin,
            customer=self.customer_one,
            title="Draft Proposal",
            status="DRAFT"
        )
        # 2. Sent quote for customer_one (Customer 1 SHOULD be able to view)
        sent_quote = Quotation.objects.create(
            created_by=self.admin,
            customer=self.customer_one,
            title="Finalized Proposal",
            status="SENT"
        )
        # 3. Sent quote for customer_two (Customer 1 should NOT be able to view)
        other_quote = Quotation.objects.create(
            created_by=self.admin,
            customer=self.customer_two,
            title="Other Client Proposal",
            status="SENT"
        )

        # Login as Customer 1
        self.client.login(username="customer1", password="custpassword")
        
        # Cannot view draft
        draft_resp = self.client.get(reverse('view_quotation_proposal', args=[draft_quote.id]))
        self.assertEqual(draft_resp.status_code, 403)
        
        # Can view sent
        sent_resp = self.client.get(reverse('view_quotation_proposal', args=[sent_quote.id]))
        self.assertEqual(sent_resp.status_code, 200)
        self.assertContains(sent_resp, "Finalized Proposal")
        
        # Cannot view other customer's quote
        other_resp = self.client.get(reverse('view_quotation_proposal', args=[other_quote.id]))
        self.assertEqual(other_resp.status_code, 403)


class LoginLogTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username="superuser",
            email="superuser@solar.com",
            password="solar123",
            role="SUPERUSER",
            is_approved=True
        )
        self.admin = User.objects.create_user(
            username="testadmin",
            email="admin@test.com",
            password="adminpassword",
            role="ADMIN",
            is_approved=True
        )
        self.staff = User.objects.create_user(
            username="teststaff",
            email="staff@test.com",
            password="staffpassword",
            role="STAFF",
            is_approved=True
        )
        self.customer = User.objects.create_user(
            username="testcustomer",
            email="customer@test.com",
            password="customerpassword",
            role="CUSTOMER",
            is_approved=True
        )

    def test_login_creates_log_entry(self):
        """Verify that a successful login creates a LoginLog entry."""
        # Initial check
        self.assertEqual(LoginLog.objects.count(), 0)
        
        # Log in
        login_success = self.client.login(username="testadmin", password="adminpassword")
        self.assertTrue(login_success)
        
        # Verify log entry is created
        self.assertEqual(LoginLog.objects.count(), 1)
        log = LoginLog.objects.first()
        self.assertEqual(log.user, self.admin)
        self.assertIsNotNone(log.login_time)

    def test_logs_visibility_in_dashboards(self):
        """Verify that only superusers and admins can see login logs on dashboards."""
        # Create some dummy logs
        LoginLog.objects.create(user=self.customer, ip_address="127.0.0.1", user_agent="Mozilla")
        LoginLog.objects.create(user=self.staff, ip_address="127.0.0.1", user_agent="Chrome")
        
        # 1. Superuser dashboard access
        self.client.login(username="superuser", password="solar123")
        response = self.client.get(reverse('superuser_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('login_logs_today', response.context)
        self.assertIn('login_logs_all', response.context)
        self.assertContains(response, "User Login Audit Logs")
        self.assertContains(response, "@testcustomer")
        self.assertContains(response, "@teststaff")
        self.client.logout()

        # 2. Admin dashboard access
        self.client.login(username="testadmin", password="adminpassword")
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('login_logs_today', response.context)
        self.assertIn('login_logs_all', response.context)
        self.assertContains(response, "User Login Audit Logs")
        self.assertContains(response, "@testcustomer")
        self.assertContains(response, "@teststaff")
        self.client.logout()

        # 3. Staff dashboard access (should not have logs)
        self.client.login(username="teststaff", password="staffpassword")
        response = self.client.get(reverse('staff_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('login_logs_today', response.context)
        self.assertNotIn('login_logs_all', response.context)
        self.assertNotContains(response, "User Login Audit Logs")
        self.client.logout()

        # 4. Customer dashboard access (should not have logs)
        self.client.login(username="testcustomer", password="customerpassword")
        response = self.client.get(reverse('customer_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('login_logs_today', response.context)
        self.assertNotIn('login_logs_all', response.context)
        self.assertNotContains(response, "User Login Audit Logs")


class InspectionWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.superuser = User.objects.create_superuser(
            username="superuser",
            email="superuser@solar.com",
            password="solar123",
            role="SUPERUSER",
            is_approved=True
        )
        
        self.admin = User.objects.create_user(
            username="adminuser",
            email="admin@test.com",
            password="adminpassword",
            role="ADMIN",
            is_approved=True
        )
        
        self.staff = User.objects.create_user(
            username="staffuser",
            email="staff@test.com",
            password="staffpassword",
            role="STAFF",
            is_approved=True,
            employee_id="STF-1234"
        )
        
        self.customer = User.objects.create_user(
            username="customeruser",
            email="customer@test.com",
            password="customerpassword",
            role="CUSTOMER",
            is_approved=True
        )
        
        self.project = SolarInstallationProject.objects.create(
            customer=self.customer,
            staff_incharge=self.staff,
            title="Inspection Test Project",
            status="SITE_SURVEY",
            total_value=150000.00,
            advances_paid=50000.00,
            start_date="2026-05-01",
            end_date="2026-05-30"
        )

    def test_project_completion_validation_without_inverter_details(self):
        """Verify that a project cannot be closed/completed without inverter brand and capacity details."""
        from django.core.exceptions import ValidationError
        self.project.status = "COMPLETED"
        with self.assertRaises(ValidationError):
            self.project.save()

    def test_project_completion_success_with_inverter_details(self):
        """Verify that project closes successfully when inverter brand/capacity are set, and creates scheduled inspection."""
        import datetime
        from django.utils import timezone
        inverter = self.project.inverter
        inverter.brand = "Sungrow"
        inverter.model = "SG5.0RS"
        inverter.serial_number = "SN12345678"
        inverter.capacity = Decimal("5.00")
        inverter.save()
        self.project.status = "COMPLETED"
        self.project.save()
        
        # Verify closing date is set
        self.assertIsNotNone(self.project.closing_date)
        
        # Verify 6-month inspection was auto-scheduled
        inspection = Inspection.objects.filter(project=self.project).first()
        self.assertIsNotNone(inspection)
        self.assertEqual(inspection.status, "SCHEDULED")
        
        closing_date = self.project.closing_date
        month = closing_date.month - 1 + 6
        year = closing_date.year + month // 12
        month = month % 12 + 1
        day = min(closing_date.day, [31,
            29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
            31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
        expected_date = datetime.date(year, month, day)
        self.assertEqual(inspection.scheduled_date, expected_date)

    def test_staff_perform_inspection_with_issues_notifies_admins(self):
        """Verify staff can perform inspection, fill checklist, report issues, and send notification to admins."""
        from django.utils import timezone
        inverter = self.project.inverter
        inverter.brand = "Sungrow"
        inverter.model = "SG5.0RS"
        inverter.serial_number = "SN12345678"
        inverter.capacity = Decimal("5.00")
        inverter.save()
        self.project.status = "COMPLETED"
        self.project.save()
        
        inspection = Inspection.objects.get(project=self.project)
        
        # Log in as Staff
        self.client.login(username="staffuser", password="staffpassword")
        
        response = self.client.post(reverse('perform_inspection', args=[inspection.id]), {
            'panel_check': True,
            'inverter_check': True,
            'wiring_check': True,
            'mounting_check': True,
            'performance_check': True,
            'has_issues': True,
            'issue_details': 'Damaged wire casing on panel 3.'
        })
        self.assertEqual(response.status_code, 302) # redirect to dashboard
        
        inspection.refresh_from_db()
        self.assertEqual(inspection.status, "COMPLETED")
        self.assertEqual(inspection.inspector, self.staff)
        self.assertTrue(inspection.has_issues)
        self.assertEqual(inspection.issue_details, 'Damaged wire casing on panel 3.')
        
        # Verify alert notification was sent to admin and superuser
        notifications = Notification.objects.filter(notification_type="ALERT")
        self.assertTrue(notifications.filter(user=self.admin).exists())
        self.assertTrue(notifications.filter(user=self.superuser).exists())

    def test_client_view_only_access(self):
        """Verify client can view inspection but cannot perform it (returns 403)."""
        inverter = self.project.inverter
        inverter.brand = "Sungrow"
        inverter.model = "SG5.0RS"
        inverter.serial_number = "SN12345678"
        inverter.capacity = Decimal("5.00")
        inverter.save()
        self.project.status = "COMPLETED"
        self.project.save()
        
        inspection = Inspection.objects.get(project=self.project)
        
        # Log in as Client
        self.client.login(username="customeruser", password="customerpassword")
        
        # Detail view should be accessible
        response = self.client.get(reverse('inspection_detail', args=[inspection.id]))
        self.assertEqual(response.status_code, 200)
        
        # Perform view should be forbidden
        perform_response = self.client.get(reverse('perform_inspection', args=[inspection.id]))
        self.assertEqual(perform_response.status_code, 403)

    def test_admin_and_superuser_can_assign_inspector(self):
        """Verify that an admin and a superuser can assign and unassign an inspector staff to a scheduled inspection."""
        inverter = self.project.inverter
        inverter.brand = "Sungrow"
        inverter.model = "SG5.0RS"
        inverter.serial_number = "SN12345678"
        inverter.capacity = Decimal("5.00")
        inverter.save()
        self.project.status = "COMPLETED"
        self.project.save()
        
        inspection = Inspection.objects.get(project=self.project)
        self.assertIsNone(inspection.inspector)
        
        # 1. Admin logs in and assigns the staff
        self.client.login(username="adminuser", password="adminpassword")
        response = self.client.post(reverse('admin_dashboard'), {
            'action': 'assign_inspector',
            'inspection_id': inspection.id,
            'inspector_id': self.staff.id
        })
        self.assertEqual(response.status_code, 302)
        
        inspection.refresh_from_db()
        self.assertEqual(inspection.inspector, self.staff)
        
        # 2. Admin unassigns the staff (inspector_id = "")
        response = self.client.post(reverse('admin_dashboard'), {
            'action': 'assign_inspector',
            'inspection_id': inspection.id,
            'inspector_id': ""
        })
        self.assertEqual(response.status_code, 302)
        
        inspection.refresh_from_db()
        self.assertIsNone(inspection.inspector)
        
        # 3. Superuser logs in and assigns the staff
        self.client.login(username="superuser", password="solar123")
        response = self.client.post(reverse('superuser_dashboard'), {
            'action': 'assign_inspector',
            'inspection_id': inspection.id,
            'inspector_id': self.staff.id
        })
        self.assertEqual(response.status_code, 302)
        
        inspection.refresh_from_db()
        self.assertEqual(inspection.inspector, self.staff)




