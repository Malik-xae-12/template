from django import forms

class PatientIdLookupForm(forms.Form):
    first_name = forms.CharField(
        label="First Name",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter First Name',
            'class': 'form-control'
        })
    )
    last_name = forms.CharField(
        label="Last Name",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter Last Name',
            'class': 'form-control'
        })
    )
    dob = forms.DateField(
        label="Date of Birth",
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    mobile = forms.CharField(
        label="Mobile Number",
        max_length=12,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter Mobile Number (xxxxxxxxxx)',
            'pattern': '[0-9]{12}',
            'title': 'Enter a 12-digit Mobile Number',
            'class': 'form-control'
        })
    )
    emirati_id = forms.CharField(
        label="Emirates ID",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder':'(xxx-xxxx-xxxxxxx-x)',
            'class': 'form-control'
        })
    )


class PatientReportSearchForm(forms.Form):
    date = forms.DateField(
        label="Date",
        required=False,  
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'Select a date'  
        })
    )
    patient_id = forms.CharField(
        max_length=100,
        label="URN",
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter URN',
            'class': 'form-control'
        })
    )


class AppointmentSearchForm(forms.Form):
    date = forms.DateField(
        label="Date",
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'Select a date'
        })
    )