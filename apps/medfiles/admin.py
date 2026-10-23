from django.contrib import admin
from .models import (
    PatientLookupHistory, PatientReportHistory, PatientReportPDFAccess,
    AppointmentFilterHistory, AppointmentFilter_ReportPDFListAccess, 
    AppointmentFilter_ReportPDFAccess
)

# Base admin that shows all fields
class AllFieldsAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.fields]

# Register all models with all-columns view
admin.site.register(PatientLookupHistory, AllFieldsAdmin)
admin.site.register(PatientReportHistory, AllFieldsAdmin)
admin.site.register(PatientReportPDFAccess, AllFieldsAdmin)
admin.site.register(AppointmentFilterHistory, AllFieldsAdmin)
admin.site.register(AppointmentFilter_ReportPDFListAccess, AllFieldsAdmin)
admin.site.register(AppointmentFilter_ReportPDFAccess, AllFieldsAdmin)
