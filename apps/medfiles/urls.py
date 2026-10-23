# urls.py - URLs for PDF tracking system
from django.urls import path
from . import views

urlpatterns = [
    # ====================== MAIN PAGE VIEWS ======================
    
    # Appointment List (with filtering)
    path('appointments/', 
         views.AppointmentListView.as_view(), 
         name='appointment_list'),
    
    # Appointment PDF List (DrugAdmin/EPR)
    path('appointments/<str:type>/<str:urn>/<str:date>/', 
         views.AppointmentPDFListView.as_view(), 
         name='appointment_pdf_list'),
     
    # Patient Report & Lookup
    path('patient-report/', 
         views.PatientReportView.as_view(), 
         name='patient_report'),
    
    
    # AJAX Search for appointments
    path('ajax-search-appointments/', 
         views.ajax_search_appointments, 
         name='ajax_search_appointments'),

     path('files/pdf/patient-report/<str:urn>/<path:filename>/', 
         views.serve_patient_report_pdf, 
         name='serve_patient_report_pdf'),
    
    
    # ====================== PDF TRACKING ENDPOINTS ======================
    
    path(
        "appointments/<str:pdf_type>/<str:urn>/<path:path>/track/",
        views.appointment_filter_pdf_access,
        name="appointment_filter_pdf_access",
    ),
    path('pdf/patient-report/<str:urn>/<path:relative_path>/', 
         views.patient_report_pdf_access, 
         name='patient_report_pdf_access'),
    
    
    
    # ====================== FALLBACK PDF SERVING ======================
    
    # Secure PDF view (fallback)
    path('secure-pdf/<path:path>/', 
         views.secure_pdf_view, 
         name='secure_pdf'),
]