import django_filters
from django import forms
from django.db.models import Q
from apps.medfiles.appointment import Appointments

class AppointmentFilter(django_filters.FilterSet):
    urn = django_filters.CharFilter(
        method='filter_urn_multiple',
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control form-control-sm select2-search',
            'id': 'id_urn',
            'data-field': 'urn',
            'data-placeholder': 'Search URNs...',
            'data-minimum-input-length': '2'
        })
    )
    
    care_provider = django_filters.CharFilter(
        method='filter_care_provider_multiple',
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control form-control-sm select2-search',
            'id': 'id_care_provider',
            'data-field': 'care_provider',
            'data-placeholder': 'Search Care Providers...',
            'data-minimum-input-length': '2'
        })
    )
    
    patient_name = django_filters.CharFilter(
        method='filter_patient_name_multiple',
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control form-control-sm select2-search',
            'id': 'id_patient_name',
            'data-field': 'patient_name',
            'data-placeholder': 'Search Patient Names...',
            'data-minimum-input-length': '2'
        })
    )
    
    location = django_filters.CharFilter(
        method='filter_location_multiple',
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control form-control-sm select2-search',
            'id': 'id_location',
            'data-field': 'location',
            'data-placeholder': 'Search Locations...',
            'data-minimum-input-length': '2'
        })
    )
    
    start_date = django_filters.DateFilter(
        field_name='start_date',
        lookup_expr='exact',
        label='Start Date',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-sm',
            'id': 'id_start_date'
        })
    )

    class Meta:
        model = Appointments
        fields = ['urn', 'care_provider', 'patient_name', 'location', 'start_date']

    def filter_urn_multiple(self, queryset, name, value):
        if not value:
            return queryset
        
        # Handle multiple values from QueryDict
        values = self.data.getlist(name) if isinstance(self.data, dict) else [value]
        values = [v.strip() for v in values if v.strip()]
        
        if not values:
            return queryset
        
        q_objects = Q()
        for val in values:
            q_objects |= Q(urn__icontains=val)
        
        return queryset.filter(q_objects)

    def filter_care_provider_multiple(self, queryset, name, value):
        if not value:
            return queryset
        
        values = self.data.getlist(name) if isinstance(self.data, dict) else [value]
        values = [v.strip() for v in values if v.strip()]
        
        if not values:
            return queryset
        
        q_objects = Q()
        for val in values:
            q_objects |= Q(care_provider__icontains=val)
        
        return queryset.filter(q_objects)

    def filter_patient_name_multiple(self, queryset, name, value):
        if not value:
            return queryset
        
        values = self.data.getlist(name) if isinstance(self.data, dict) else [value]
        values = [v.strip() for v in values if v.strip()]
        
        if not values:
            return queryset
        
        q_objects = Q()
        for val in values:
            q_objects |= Q(patient_name__icontains=val)
        
        return queryset.filter(q_objects)

    def filter_location_multiple(self, queryset, name, value):
        if not value:
            return queryset
        
        values = self.data.getlist(name) if isinstance(self.data, dict) else [value]
        values = [v.strip() for v in values if v.strip()]
        
        if not values:
            return queryset
        
        q_objects = Q()
        for val in values:
            q_objects |= Q(location__icontains=val)
        
        return queryset.filter(q_objects)

    @property
    def qs(self):
        """Override to ensure we always get distinct results ordered by start_date DESC"""
        parent_qs = super().qs
        return parent_qs.distinct().order_by('-start_date', '-id')