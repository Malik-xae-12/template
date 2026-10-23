from django.db import models
from django.contrib.auth import get_user_model
from apps.medfiles.utils.timezone import now_dubai   # 👈 using Dubai time always

User = get_user_model()

class PatientLookupHistory(models.Model):
    """Track patient lookup searches"""
    lookup_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="patient_lookups", db_index=True)
    
    # Search criteria used
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    mobile_number = models.CharField(max_length=20, blank=True)
    emirates_id = models.CharField(max_length=50, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Search results
    patients_found_count = models.IntegerField(default=0)
    search_successful = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=now_dubai, db_index=True)

    def __str__(self):
        return f"{self.user.username} - Patient Lookup - {self.created_at}"

    class Meta:
        db_table = 'patient_lookup_history'
        ordering = ['-created_at']
        verbose_name = "Patient Search"
        verbose_name_plural = "Patient Searches"
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]


class PatientReportHistory(models.Model):
    """Track patient report searches and PDF access"""
    report_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="patient_reports", db_index=True)
    
    # Report search criteria
    urn = models.CharField(max_length=100, db_index=True)
    report_date = models.DateField(null=True, blank=True)
    
    # Results found
    total_pdfs_found = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(default=now_dubai, db_index=True)

    def __str__(self):
        return f"{self.user.username} - Report for {self.urn} on {self.report_date}"

    class Meta:
        db_table = 'patient_report_history'
        ordering = ['-created_at']
        verbose_name = "Patient Report"
        verbose_name_plural = "Patient Reports"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['urn', 'report_date']),
        ]


class PatientReportPDFAccess(models.Model):
    """Track which specific PDFs user opened from patient reports"""
    access_id = models.AutoField(primary_key=True)
    patient_report = models.ForeignKey(PatientReportHistory, on_delete=models.CASCADE, related_name="pdf_accesses")
    
    pdf_name = models.CharField(max_length=255)
    pdf_path = models.CharField(max_length=500)
    
    accessed_at = models.DateTimeField(default=now_dubai)

    def __str__(self):
        return f"{self.patient_report.user.username} - {self.pdf_name}"

    class Meta:
        db_table = 'patient_report_pdf_access'
        ordering = ['-accessed_at']
        verbose_name = "Patient PDF View"
        verbose_name_plural = "Patient PDF Views"


# class AppointmentReportHistory(models.Model):
#     """Track appointment report searches by date"""
#     appointment_report_id = models.AutoField(primary_key=True)
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="appointment_reports", db_index=True)
    
#     appointment_date = models.DateField()
#     total_pdfs_found = models.IntegerField(default=0)
    
#     created_at = models.DateTimeField(default=now_dubai, db_index=True)

#     def __str__(self):
#         return f"{self.user.username} - Appointment Report for {self.appointment_date}"

#     class Meta:
#         db_table = 'appointment_report_history'
#         ordering = ['-created_at']
#         verbose_name = "Appointment Report"
#         verbose_name_plural = "Appointment Reports"
#         indexes = [
#             models.Index(fields=['user', '-created_at']),
#             models.Index(fields=['appointment_date']),
#         ]


# class AppointmentReportPDFAccess(models.Model):
#     """Track which specific PDFs user opened from appointment reports"""
#     access_id = models.AutoField(primary_key=True)
#     appointment_report = models.ForeignKey(AppointmentReportHistory, on_delete=models.CASCADE, related_name="pdf_accesses")
    
#     pdf_name = models.CharField(max_length=255)
#     pdf_path = models.CharField(max_length=500)
    
#     accessed_at = models.DateTimeField(default=now_dubai)

#     def __str__(self):
#         return f"{self.appointment_report.user.username} - {self.pdf_name}"

#     class Meta:
#         db_table = 'appointment_report_pdf_access'
#         ordering = ['-accessed_at']
#         verbose_name = "Appointment PDF View"
#         verbose_name_plural = "Appointment PDF Views"



class AppointmentFilterHistory(models.Model):
    """Track appointment filter applications"""
    filter_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="appointment_filters", db_index=True)
    
    # Filter criteria applied
    urn_filter = models.CharField(max_length=50, blank=True)
    care_provider_filter = models.CharField(max_length=255, blank=True)
    patient_name_filter = models.CharField(max_length=255, blank=True)
    location_filter = models.CharField(max_length=255, blank=True)
    start_date_filter = models.DateField(null=True, blank=True)
    
    # Filter results
    total_records_found = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(default=now_dubai, db_index=True)

    def __str__(self):
        return f"{self.user.username} - Appointment Filter - {self.created_at}"

    class Meta:
        db_table = 'appointment_filter_history'
        ordering = ['-created_at']
        verbose_name = "Appointment Filter"
        verbose_name_plural = "Appointment Filters"
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]


class AppointmentFilter_ReportPDFListAccess(models.Model):
    """Track when user clicks DrugAdmin or EPR links from appointment list"""
    PDF_TYPES = [
        ('drugadmin', 'Drug Admin'),
        ('epr', 'EPR'),
    ]
    
    list_access_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="appointment_filter_pdf_lists", db_index=True)
    
    pdf_type = models.CharField(max_length=20, choices=PDF_TYPES)
    urn = models.CharField(max_length=50)
    appointment_date = models.DateField()
    total_pdfs_found = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(default=now_dubai, db_index=True)

    def __str__(self):
        return f"{self.user.username} - {self.pdf_type.upper()} List for {self.urn}"

    class Meta:
        db_table = 'appointment_filter_report_pdf_list_access'
        ordering = ['-created_at']
        verbose_name = "DrugAdmin/EPR List View"
        verbose_name_plural = "DrugAdmin/EPR List Views"
        indexes = [
            models.Index(fields=['user', 'pdf_type', '-created_at']),
            models.Index(fields=['urn', '-created_at']),
        ]


class AppointmentFilter_ReportPDFAccess(models.Model):
    """Track which specific PDFs user opened from DrugAdmin/EPR lists"""
    access_id = models.AutoField(primary_key=True)
    pdf_list_access = models.ForeignKey(AppointmentFilter_ReportPDFListAccess, on_delete=models.CASCADE, related_name="pdf_accesses")
    
    pdf_name = models.CharField(max_length=255)
    pdf_path = models.CharField(max_length=500)
    
    accessed_at = models.DateTimeField(default=now_dubai)

    def __str__(self):
        return f"{self.pdf_list_access.user.username} - {self.pdf_name}"

    class Meta:
        db_table = 'appointment_filter_report_pdf_access'
        ordering = ['-accessed_at']
        verbose_name = "DrugAdmin/EPR PDF View"
        verbose_name_plural = "DrugAdmin/EPR PDF Views"
