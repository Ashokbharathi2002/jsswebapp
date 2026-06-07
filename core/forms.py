from django import forms
from .models import CustomUser, SolarInstallationProject, Complaint, Quotation, ProjectExpense

class CustomerSignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'whatsapp_number']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number (e.g. +1234567890)'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'WhatsApp Number (e.g. +1234567890)'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = 'CUSTOMER'
        user.is_approved = False  # Explicitly false, needs admin approval!
        if commit:
            user.save()
        return user


class StaffCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'whatsapp_number', 'employee_id', 'bio', 'salary']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional - Auto-generated if left blank'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Monthly base salary'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = 'STAFF'
        user.is_approved = True  # Automatically approved (Admin created)
        if commit:
            user.save()
        return user


class EmployeeCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'whatsapp_number', 'employee_id', 'bio', 'salary']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional - Auto-generated if left blank'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Monthly base salary'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = 'EMPLOYEE'
        user.is_approved = True  # Automatically approved (Admin created)
        if commit:
            user.save()
        return user


class StaffSignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'whatsapp_number', 'bio']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'WhatsApp Contact'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your background and expertise...'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = 'STAFF'
        user.is_approved = False  # Requires Admin Approval!
        if commit:
            user.save()
        return user


class AdminCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'whatsapp_number', 'bio']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = 'ADMIN'
        user.is_approved = True
        if commit:
            user.save()
        return user


class AdminCustomerCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'whatsapp_number']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = 'CUSTOMER'
        user.is_approved = True  # Admin created client is pre-approved!
        if commit:
            user.save()
        return user


class ProjectForm(forms.ModelForm):
    class Meta:
        model = SolarInstallationProject
        fields = [
            'customer', 'staff_incharge', 'title', 'status', 
            'advances_paid', 'total_value', 'start_date', 'end_date', 
            'laborers_count', 'crew_details'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'staff_incharge': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'advances_paid': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'laborers_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'crew_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g. John (Lead), EMP-1002 (Helper)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = CustomUser.objects.filter(role='CUSTOMER')
        self.fields['staff_incharge'].queryset = CustomUser.objects.filter(role='STAFF')


class StaffProjectUpdateForm(forms.ModelForm):
    class Meta:
        model = SolarInstallationProject
        fields = ['status', 'laborers_count', 'crew_details']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'laborers_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'crew_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class StaffEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'whatsapp_number', 'employee_id', 'bio', 'salary']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Monthly base salary'}),
        }


class EmployeeEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'whatsapp_number', 'employee_id', 'bio', 'salary']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Monthly base salary'}),
        }


class ClientEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'whatsapp_number']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['subject', 'description']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter the subject/title of the issue...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your issue in detail here...'}),
        }


class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = [
            'customer', 'lead_name', 'lead_email', 'lead_phone',
            'title', 'solar_capacity_kw', 'material_breakdown',
            'material_cost', 'labor_cost', 'tax_cost', 'total_price', 'status'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'lead_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional - For unregistered leads'}),
            'lead_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Optional - lead email'}),
            'lead_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional - lead phone'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 5kW Solar Array Installation'}),
            'solar_capacity_kw': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'material_breakdown': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g. 12x 450W Mono panels, 5kW Grid-tie Inverter...'}),
            'material_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'labor_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Leave blank to auto-calculate sum'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = CustomUser.objects.filter(role='CUSTOMER')
        self.fields['total_price'].required = False

    def clean(self):
        cleaned_data = super().clean()
        customer = cleaned_data.get('customer')
        lead_name = cleaned_data.get('lead_name')
        if not customer and not lead_name:
            raise forms.ValidationError("Please select a registered customer OR enter a lead name for unregistered clients.")
        return cleaned_data


class ProjectExpenseForm(forms.ModelForm):
    class Meta:
        model = ProjectExpense
        fields = ['project', 'title', 'amount', 'date', 'notes']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter expense title (e.g. Copper wiring purchase)'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter additional notes...'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            if user.role == 'STAFF':
                self.fields['project'].queryset = SolarInstallationProject.objects.filter(staff_incharge=user)
            elif user.role in ['ADMIN', 'SUPERUSER'] or user.is_superuser:
                self.fields['project'].queryset = SolarInstallationProject.objects.all()

