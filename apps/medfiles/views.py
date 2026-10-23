# views.py - Updated with direct PDF access tracking (no sessions)
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.contrib.auth.decorators import login_required
from .filters import AppointmentFilter
from .models import (
    PatientLookupHistory, PatientReportHistory, PatientReportPDFAccess,
    AppointmentFilterHistory, AppointmentFilter_ReportPDFListAccess, 
    AppointmentFilter_ReportPDFAccess
)
from .appointment import Appointments
from .forms import PatientIdLookupForm, PatientReportSearchForm, AppointmentSearchForm
from .services.patient_helper import getpatid
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import JsonResponse
from django.db.models import Q
import os
import glob
from datetime import datetime
import logging
from django.http import FileResponse, Http404, JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import urllib.parse

# Set up logging
logger = logging.getLogger(__name__)

# views.py - Updated Patient Report View with PDF Grouping

def get_patient_report_path_grouped(base_dir, urn, date_yyyymmdd=None):
    """Helper function to get grouped patient report paths by timestamp"""
    grouped_reports = {}
    
    try:
        if urn and date_yyyymmdd:
            # Case 1: URN + Date → search in specific date folder
            pattern = os.path.join(base_dir, f"{date_yyyymmdd}-*", urn, "*.pdf")
        elif urn:
            # Case 2: URN only → search across ALL date folders
            pattern = os.path.join(base_dir, "*", urn, "*.pdf")
        else:
            return grouped_reports
            
        report_paths = glob.glob(pattern)
        
        for path in report_paths:
            if os.path.exists(path) and os.path.isfile(path):
                # Extract folder info: E:\TC_BC\Reports\20250327-090000\468511\DrugAdmin.pdf
                folder_name = os.path.basename(os.path.dirname(os.path.dirname(path)))
                filename = os.path.basename(path)
                
                # Parse folder name: 20250327-090000
                if '-' in folder_name:
                    date_part, time_part = folder_name.split('-', 1)
                    
                    # Format date: 20250327 -> 2025-03-27
                    try:
                        formatted_date = datetime.strptime(date_part, '%Y%m%d').strftime('%Y-%m-%d')
                    except ValueError:
                        formatted_date = date_part
                    
                    # Format time: 090000 -> 09:00:00
                    if len(time_part) == 6:
                        formatted_time = f"{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                    else:
                        formatted_time = time_part
                    
                    # Create unique key for grouping
                    timestamp_key = f"{date_part}-{time_part}"
                    
                    if timestamp_key not in grouped_reports:
                        grouped_reports[timestamp_key] = {
                            'folder_path': os.path.dirname(path),
                            'date': formatted_date,
                            'time': formatted_time,
                            'raw_date': date_part,
                            'raw_time': time_part,
                            'drugadmin': None,
                            'epr': None
                        }

                    rel_path = os.path.relpath(path,base_dir).replace("\\","/")

                    
                    # Categorize PDF type
                    if filename.lower().startswith('drugadmin'):
                        grouped_reports[timestamp_key]['drugadmin'] = {
                            'filename': filename,
                            'path': path.replace('\\', '/'),
                            'rel_path':rel_path,
                        }
                    elif filename.lower().startswith('epr'):
                        grouped_reports[timestamp_key]['epr'] = {
                            'filename': filename,
                            'path': path.replace('\\', '/'),
                            'rel_path':rel_path,
                        }
        
        logger.info(f"Found {len(grouped_reports)} grouped reports for URN {urn}")
        
    except Exception as e:
        logger.error(f"Error in get_patient_report_path_grouped: {str(e)}")
    
    # Sort by date and time (newest first)
    sorted_reports = dict(sorted(
        grouped_reports.items(), 
        key=lambda x: (x[1]['raw_date'], x[1]['raw_time']), 
        reverse=True
    ))
    
    return sorted_reports

class PatientReportView(LoginRequiredMixin, View):
    login_url = '/login/'
    template_name = 'patient_report_lookup.html'

    def get(self, request, *args, **kwargs):
        report_search_form = PatientReportSearchForm()
        patient_lookup_form = PatientIdLookupForm()
        patient_id_result = None
        patient_records = []
        grouped_reports = {}
        no_patient_found = False

        if 'patient_records' in request.session:
            del request.session['patient_records']

        # Get recent histories with unique urn and report_date
        try:
            raw_history = PatientReportHistory.objects.filter(user=request.user).values('urn', 'report_date', 'user__username')
            unique_history = []
            seen = set()
            for entry in raw_history:
                key = (entry['urn'], entry['report_date'])
                if key not in seen:
                    seen.add(key)
                    unique_history.append(entry)
            patient_report_history = unique_history
            patient_lookup_history = PatientLookupHistory.objects.filter(user=request.user)[:10]
        except Exception as history_error:
            logger.error(f"Error fetching histories: {str(history_error)}")
            patient_report_history = []
            patient_lookup_history = []

        context = {
            'patient_lookup_form': patient_lookup_form,
            'report_search_form': report_search_form,
            'patient_id_result': patient_id_result,
            'patient_records': patient_records,
            'grouped_reports': grouped_reports,
            'title': 'Patient Report & Lookup',
            'no_patient_found': no_patient_found,
            'patient_lookup_history': patient_lookup_history,
            'patient_report_history': patient_report_history
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        report_search_form = PatientReportSearchForm()
        patient_lookup_form = PatientIdLookupForm()
        patient_id_result = None
        patient_records = []
        grouped_reports = {}
        no_patient_found = False
        error_message = None

        # Handle session data safely
        try:
            if 'patient_records' in request.session:
                patient_records = request.session['patient_records']
                patient_id_result = patient_records[0].get('PAPMI_No', "Not found") if patient_records else "Not found"
        except Exception as session_error:
            logger.error(f"Session error: {str(session_error)}")
            patient_records = []
            patient_id_result = None

        try:
            if 'submit_id' in request.POST:  # Patient Report Search
                report_search_form = PatientReportSearchForm(request.POST)
                if report_search_form.is_valid():
                    urn = report_search_form.cleaned_data['patient_id']
                    date_obj = report_search_form.cleaned_data['date']
                    date_yyyymmdd = date_obj.strftime('%Y%m%d') if date_obj else None

                    try:
                        base_dir = os.path.join(settings.MEDIA_ROOT, "Reports")

                        if urn:
                            grouped_reports = get_patient_report_path_grouped(base_dir, urn, date_yyyymmdd)
                            
                            total_pdfs = 0
                            for group in grouped_reports.values():
                                if group['drugadmin']:
                                    total_pdfs += 1
                                if group['epr']:
                                    total_pdfs += 1

                            report_date = date_obj if date_obj else None

                            try:
                                PatientReportHistory.objects.create(
                                    user=request.user,
                                    urn=urn,
                                    report_date=report_date,
                                    total_pdfs_found=total_pdfs
                                )
                                log_message = f"Logged patient report search: URN {urn}"
                                log_message += f" on {report_date.strftime('%Y-%m-%d')}" if report_date else " (all dates)"
                                logger.info(log_message)
                            except Exception as log_error:
                                logger.error(f"Error logging patient report: {str(log_error)}")

                        else:
                            grouped_reports = {}

                    except Exception as search_error:
                        logger.error(f"Error in report search: {str(search_error)}")
                        grouped_reports = {}

                else:
                    logger.error(f"Report form validation failed: {report_search_form.errors}")

            elif 'submit_details' in request.POST:  # Patient Lookup
                patient_lookup_form = PatientIdLookupForm(request.POST)
                if patient_lookup_form.is_valid():
                    filter_fields = {}
                    
                    try:
                        if patient_lookup_form.cleaned_data.get('dob'):
                            filter_fields['PAPMI_DOB'] = patient_lookup_form.cleaned_data['dob'].strftime('%Y-%m-%d')
                        if patient_lookup_form.cleaned_data.get('mobile'):
                            filter_fields['PAPMI_MobPhone'] = patient_lookup_form.cleaned_data['mobile']
                        if patient_lookup_form.cleaned_data.get('first_name'):
                            filter_fields['first_name'] = patient_lookup_form.cleaned_data['first_name']
                        if patient_lookup_form.cleaned_data.get('last_name'):
                            filter_fields['last_name'] = patient_lookup_form.cleaned_data['last_name']
                        if patient_lookup_form.cleaned_data.get('emirati_id'):
                            filter_fields['PAPMI_ID'] = patient_lookup_form.cleaned_data['emirati_id']
                    except Exception as filter_error:
                        logger.error(f"Error building filter fields: {str(filter_error)}")
                        filter_fields = {}

                    try:
                        patient_records = getpatid(filter_fields)

                        try:
                            PatientLookupHistory.objects.create(
                                user=request.user,
                                first_name=patient_lookup_form.cleaned_data.get('first_name', ''),
                                last_name=patient_lookup_form.cleaned_data.get('last_name', ''),
                                mobile_number=patient_lookup_form.cleaned_data.get('mobile', ''),
                                emirates_id=patient_lookup_form.cleaned_data.get('emirati_id', ''),
                                date_of_birth=patient_lookup_form.cleaned_data.get('dob'),
                                patients_found_count=len(patient_records) if patient_records else 0,
                                search_successful=bool(patient_records)
                            )
                            logger.info(f"Logged patient lookup by {request.user.username}")
                        except Exception as log_error:
                            logger.error(f"Error logging patient lookup: {str(log_error)}")

                        try:
                            if patient_records == "GraphQL internal error":
                                error_message = "GraphQL internal error"
                                patient_records = []
                            elif patient_records:
                                patient_id_result = patient_records[0].get('PAPMI_No', "Not found")
                                no_patient_found = False
                                request.session['patient_records'] = patient_records
                            else:
                                patient_id_result = "Not found"
                                no_patient_found = True
                                if 'patient_records' in request.session:
                                    del request.session['patient_records']
                        except Exception as result_error:
                            logger.error(f"Error handling lookup results: {str(result_error)}")
                            no_patient_found = True
                            patient_id_result = "Error occurred"

                    except Exception as lookup_error:
                        logger.error(f"Error in patient lookup: {str(lookup_error)}")
                        no_patient_found = True
                        patient_id_result = "Error occurred"

        except Exception as general_error:
            logger.error(f"General error in PatientReportView.post: {str(general_error)}")

        try:
            # Fetch all patient report history and filter for unique urn and report_date
            raw_history = PatientReportHistory.objects.filter(user=request.user).values('urn', 'report_date', 'user__username')
            unique_history = []
            seen = set()
            for entry in raw_history:
                key = (entry['urn'], entry['report_date'])
                if key not in seen:
                    seen.add(key)
                    unique_history.append(entry)
            patient_report_history = unique_history
            patient_lookup_history = PatientLookupHistory.objects.filter(user=request.user)[:10]
        except Exception as history_error:
            logger.error(f"Error fetching histories: {str(history_error)}")
            patient_report_history = []
            patient_lookup_history = []

        context = {
            'patient_lookup_form': patient_lookup_form,
            'report_search_form': report_search_form,
            'patient_id_result': patient_id_result,
            'patient_records': patient_records,
            'grouped_reports': grouped_reports,
            'title': 'Patient Report & Lookup',
            'no_patient_found': no_patient_found,
            'patient_lookup_history': patient_lookup_history,
            'patient_report_history': patient_report_history,
            'error_message': error_message
        }

        return render(request, self.template_name, context)

@login_required
def serve_patient_report_pdf(request,folder, urn, pdf_name):
    """Serve patient report PDFs from the file system."""
    # Construct the file path (adjust based on your actual directory structure)
    base_dir = "E:/TC_BC/Reports"  
    file_path = os.path.join(base_dir,folder, urn, pdf_name.replace('/', os.sep))
    print(file_path)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    raise Http404("PDF not found")

def get_appointment_report_path(base_dir, date_yyyymmdd):
    """Helper function to get appointment report paths - simplified to return 3 values"""
    report_paths_display = []    
    try:               
        pattern = os.path.join(base_dir, f"{date_yyyymmdd}-*", "*.pdf") 
        # Use glob to find matching files
        report_paths = glob.glob(pattern)
        
        for path in report_paths:
            try:
                if os.path.exists(path) and os.path.isfile(path):
                    filename = os.path.basename(path)
                    relative_path = os.path.relpath(path, base_dir).replace('\\', '/')
                    folder_path = os.path.dirname(path)
                    report_paths_display.append((folder_path, relative_path, filename))
            except Exception as file_error:
                logger.error(f"Error processing file {path}: {str(file_error)}")
                continue
        
        logger.info(f"Found {len(report_paths_display)} appointment reports for date {date_yyyymmdd}")
        
    except Exception as e:
        logger.error(f"Error in get_appointment_report_path: {str(e)}")
    
    return report_paths_display


# class AppointmentReportView(LoginRequiredMixin, View):
#     login_url = '/login/'
#     template_name = 'appointment_report_lookup.html'

#     def get(self, request, *args, **kwargs):
#         appointment_search_form = AppointmentSearchForm()
#         report_paths = []
#         appointment_history = []
        
#         # Safely get appointment history
#         try:
#             appointment_history = list(AppointmentReportHistory.objects.filter(user=request.user)[:10])
#         except Exception as e:
#             logger.error(f"Error fetching appointment history: {str(e)}")
#             appointment_history = []

#         context = {
#             'appointment_search_form': appointment_search_form,
#             'report_paths': report_paths,
#             'title': 'Search Appointment by Date',
#             'appointment_history': appointment_history
#         }
#         return render(request, self.template_name, context)

#     def post(self, request, *args, **kwargs):
#         appointment_search_form = AppointmentSearchForm(request.POST)
#         report_paths = []
#         appointment_history = []
#         error_message = None

#         try:
#             if appointment_search_form.is_valid():
#                 date = appointment_search_form.cleaned_data['date']
#                 date_yyyymmdd = date.strftime('%Y%m%d') 
#                 base_dir = "E:/TC_BC/Appointments"                
                
#                 # Search for reports
#                 try:
#                     report_paths = get_appointment_report_path(base_dir, date_yyyymmdd)
#                     logger.info(f"Found {len(report_paths)} appointment reports for date {date}")
#                 except Exception as e:
#                     logger.error(f"Error searching for appointment reports: {str(e)}")
#                     report_paths = []
#                     error_message = f"Error searching for reports: {str(e)}"
                
#                 # 🎯 FIXED: ALWAYS CREATE NEW RECORD (remove get_or_create)
#                 try:
#                     AppointmentReportHistory.objects.create(
#                         user=request.user,
#                         appointment_date=date,
#                         total_pdfs_found=len(report_paths)
#                     )
#                     logger.info(f"Logged appointment report search for {date} by {request.user.username} - Found {len(report_paths)} PDFs")
#                 except Exception as e:
#                     logger.error(f"Error logging appointment report: {str(e)}")

#             else:
#                 error_message = "Invalid form data. Please check your input."

#         except Exception as e:
#             logger.error(f"General error in AppointmentReportView.post: {str(e)}")
#             error_message = "An unexpected error occurred. Please try again."

#         # Safely get appointment history
#         try:
#             appointment_history = list(AppointmentReportHistory.objects.filter(user=request.user)[:10])
#         except Exception as e:
#             logger.error(f"Error fetching appointment history: {str(e)}")
#             appointment_history = []

#         context = {
#             'appointment_search_form': appointment_search_form,
#             'report_paths': report_paths,
#             'title': 'Search Appointment by Date',
#             'appointment_history': appointment_history
#         }
        
#         if error_message:
#             context['error_message'] = error_message

#         return render(request, self.template_name, context)

class AppointmentListView(LoginRequiredMixin, View):
    login_url = '/login/'
    template_name = 'appointment_list.html'

    def get(self, request, *args, **kwargs):
        try:
            has_filters = any(
                key in request.GET and request.GET.getlist(key)
                for key in ['urn', 'care_provider', 'patient_name', 'location', 'start_date']
            )

            if not has_filters or 'initial_load' in request.GET:
                appointments = (
                    Appointments.objects
                    .only('urn', 'care_provider', 'patient_name', 'gender', 'location',
                          'start_date', 'timestamp', 'pdf_path', 'id')
                    .order_by('-start_date', '-id')
                )
                filter_set = AppointmentFilter()
            else:
                filter_set = AppointmentFilter(request.GET, queryset=Appointments.objects.all())
                appointments = (
                    filter_set.qs
                    .only('urn', 'care_provider', 'patient_name', 'gender',
                          'location', 'start_date', 'timestamp', 'pdf_path', 'id')
                    .order_by('-start_date', '-id')
                )

            paginator = Paginator(appointments, 20)
            page_number = request.GET.get('page', 1)
            try:
                page_obj = paginator.page(page_number)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)

            if has_filters:
                try:
                    AppointmentFilterHistory.objects.create(
                        user=request.user,
                        urn_filter=','.join(request.GET.getlist('urn', [])),
                        care_provider_filter=','.join(request.GET.getlist('care_provider', [])),
                        patient_name_filter=','.join(request.GET.getlist('patient_name', [])),
                        location_filter=','.join(request.GET.getlist('location', [])),
                        start_date_filter=datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
                            if request.GET.get('start_date') else None,
                        total_records_found=paginator.count
                    )
                except Exception as e:
                    logger.error(f"Error logging appointment filter: {str(e)}")

            # Normalize pdf_path for current page
            for appointment in page_obj:
                if appointment.pdf_path and appointment.pdf_path.startswith('E:/TC_BC/'):
                    appointment.pdf_path = os.path.relpath(appointment.pdf_path, 'E:/TC_BC').replace('\\', '/')

            # Fast per-row PDF existence flags to control icons
            reports_base = os.path.join(settings.MEDIA_ROOT, "Reports")

            def any_pdf(prefix, date_obj, urn):
                try:
                    if not date_obj or not urn:
                        return False
                    ymd = date_obj.strftime('%Y%m%d')
                    pattern = os.path.join(reports_base, f"{ymd}-*", str(urn), f"{prefix}*.pdf")
                    return any(glob.iglob(pattern))
                except Exception as e:
                    logger.error(f"PDF existence check error: {e}")
                    return False

            for appt in page_obj:
                appt.drugadmin_any = any_pdf("DrugAdmin", appt.start_date, appt.urn)
                appt.epr_any = any_pdf("EPR", appt.start_date, appt.urn)

            context = {
                'filter': filter_set,
                'appointments': page_obj,
                'title': 'Appointment Lookup',
                'has_filters': has_filters,
            }
            return render(request, self.template_name, context)

        except Exception as e:
            logger.error(f"Error in AppointmentListView: {str(e)}")
            context = {
                'filter': AppointmentFilter(),
                'appointments': Appointments.objects.none(),
                'title': 'Appointment Lookup',
                'has_filters': False,
                'error': 'An error occurred while loading appointments. Please try again.',
            }
            return render(request, self.template_name, context)


@login_required
def ajax_search_appointments(request):
    """AJAX endpoint for searching appointment options"""
    try:
        field = request.GET.get('field')
        term = request.GET.get('term', '').strip()
        
        if not field or len(term) < 2:
            return JsonResponse({'results': []})
        
        field_mapping = {
            'urn': 'urn',
            'care_provider': 'care_provider', 
            'patient_name': 'patient_name',
            'location': 'location'
        }
        
        if field not in field_mapping:
            return JsonResponse({'results': []})
        
        db_field = field_mapping[field]
        
        filter_kwargs = {f'{db_field}__icontains': term}
        
        results = (
            Appointments.objects
            .filter(**filter_kwargs)
            .exclude(**{f'{db_field}__isnull': True})
            .exclude(**{f'{db_field}__exact': ''})
            .values_list(db_field, flat=True)
            .distinct()
            .order_by(db_field)[:50]
        )
        
        formatted_results = [{'id': result, 'text': result} for result in results if result]
        
        return JsonResponse({'results': formatted_results})
        
    except Exception as e:
        logger.error(f"Error in ajax_search_appointments: {str(e)}")
        return JsonResponse({'results': []})


class AppointmentPDFListView(LoginRequiredMixin, View):
    login_url = '/login/'
    template_name = 'appointment_pdf_list.html'

    def get(self, request, type, urn, date, *args, **kwargs):
        if type not in ['drugadmin', 'epr']:
            raise Http404("Invalid PDF type")

        pdf_type = "DrugAdmin" if type == "drugadmin" else "EPR"
        base_dir = os.path.join(settings.MEDIA_ROOT, "Reports")
        
        # Convert date format from YYYY-MM-DD to YYYYMMDD for directory search
        try:
            if isinstance(date, str):
                if '-' in date:
                    date_obj = datetime.strptime(date, '%Y-%m-%d')
                    date_yyyymmdd = date_obj.strftime('%Y%m%d')
                else:
                    date_yyyymmdd = date
                    date_obj = datetime.strptime(date, '%Y%m%d')
            else:
                date_obj = date
                date_yyyymmdd = date.strftime('%Y%m%d') if date else None
        except ValueError:
            logger.error(f"Invalid date format: {date}")
            date_yyyymmdd = date
            date_obj = datetime.now().date()
        
        # Search pattern: YYYYMMDD-HHMMSS directories
        pattern = os.path.join(base_dir, f"{date_yyyymmdd}-*", urn, f"{pdf_type}*.pdf")
        report_paths = glob.glob(pattern)

        report_paths_display = []
        for path in report_paths:
            if os.path.exists(path):
                filename = os.path.basename(path)
                relative_path = os.path.relpath(path, base_dir).replace('\\', '/')
                folder_path = os.path.dirname(path)
                # Extract date and time from folder name (e.g., 20240116-090000)
                folder_name = os.path.basename(os.path.dirname(os.path.dirname(path)))
                date_time_parts = folder_name.split("-")
                if len(date_time_parts) == 2:
                    date_str = date_time_parts[0]  # e.g., "20240116"
                    time_str = date_time_parts[1]  # e.g., "090000"
                    # Format date and time for display
                    try:
                        date_formatted = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
                        time_formatted = datetime.strptime(time_str, '%H%M%S').strftime('%H:%M:%S')
                    except ValueError:
                        date_formatted = date_str
                        time_formatted = time_str
                else:
                    date_formatted = date_yyyymmdd
                    time_formatted = "00:00:00"
                report_paths_display.append((folder_path, relative_path, filename, date_formatted, time_formatted))

        # Log PDF list access
        try:
            pdf_list_access = AppointmentFilter_ReportPDFListAccess.objects.create(
                user=request.user,
                pdf_type=type,
                urn=urn,
                appointment_date=date_obj.date() if hasattr(date_obj, 'date') else date_obj,
                total_pdfs_found=len(report_paths_display)
            )
            logger.info(f"Logged PDF list access: {type} for URN {urn} by {request.user.username}")
        except Exception as e:
            logger.error(f"Error logging PDF list access: {str(e)}")

        context = {
            'pdf_type': pdf_type,
            'urn': urn,
            'date': date,
            'date_yyyymmdd': date_yyyymmdd,
            'search_pattern': pattern,
            'report_paths': report_paths_display,
            'title': f'{pdf_type} PDF List for URN {urn}'
        }
        return render(request, self.template_name, context)

@login_required
def appointment_filter_pdf_access(request, pdf_type, urn, path):
    """Direct PDF access with tracking for appointment filter PDFs (DrugAdmin/EPR)"""    
    if request.method == 'GET':
        try:
            base_dir = "E:/TC_BC/Reports"
            file_path = os.path.join(base_dir, path.replace("/", os.sep))

            if not os.path.exists(file_path):
                logger.error(f"Appointment filter PDF not found at path: {file_path}")
                raise Http404("PDF file not found")

            # 🎯 Extract date from relative path (first part of folder, e.g. 20240116-090000 → 2024-01-16)
            folder_name = path.split("/")[0]  # e.g., 20240116-090000
            date_str = folder_name.split("-")[0]  # "20240116"
            date_obj = datetime.strptime(date_str, "%Y%m%d").date()

            # 🎯 Count all PDFs of this type for the date/urn
            pdf_type_pattern = "DrugAdmin" if pdf_type.lower() == "drugadmin" else "EPR"
            all_pdfs_pattern = os.path.join(base_dir, f"{date_str}-*", urn, f"{pdf_type_pattern}*.pdf")
            total_pdfs_count = len(glob.glob(all_pdfs_pattern))

            # 🎯 Get or create latest PDF list access
            try:
                pdf_list_access = AppointmentFilter_ReportPDFListAccess.objects.filter(
                    user=request.user,
                    pdf_type=pdf_type,
                    urn=urn,
                    appointment_date=date_obj
                ).latest('created_at')
            except AppointmentFilter_ReportPDFListAccess.DoesNotExist:
                pdf_list_access = AppointmentFilter_ReportPDFListAccess.objects.create(
                    user=request.user,
                    pdf_type=pdf_type,
                    urn=urn,
                    appointment_date=date_obj,
                    total_pdfs_found=total_pdfs_count
                )

            # 🎯 Log PDF access
            AppointmentFilter_ReportPDFAccess.objects.create(
                pdf_list_access=pdf_list_access,
                pdf_name=os.path.basename(file_path),
                pdf_path=file_path.replace("\\", "/")
            )
            # 🎯 Return file
            response = FileResponse(open(file_path, "rb"), content_type="application/pdf")
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Content-Disposition'] = f'inline; filename=\"{os.path.basename(file_path)}\"'
            return response

        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Error in appointment_filter_pdf_access: {str(e)}")
            raise Http404("Error accessing PDF")

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def patient_report_pdf_access(request, urn, relative_path):
    """Direct PDF access with tracking for patient reports"""
    base_dir = "E:/TC_BC/Reports"
    full_path = os.path.join(base_dir, relative_path.replace("/", os.sep))
    if os.path.exists(full_path):
        pdf_name = os.path.basename(full_path)
        patient_report = PatientReportHistory.objects.filter(
            user=request.user,
            urn=urn
        ).latest('created_at')
        PatientReportPDFAccess.objects.create(
            patient_report=patient_report,
            pdf_name=pdf_name,
            pdf_path=full_path.replace("\\", "/")
        )
        response = FileResponse(open(full_path, "rb"), content_type="application/pdf")
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Content-Disposition'] = f'inline; filename="{pdf_name}"'
        return response
    raise Http404("PDF not found")


# @login_required
# def appointment_report_pdf_access(request, date, pdf_name):
#     """Direct PDF access with tracking for appointment reports"""
#     if request.method == 'GET':
#         try:
#             date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            
#             # 🎯 GET THE MOST RECENT history record for this user and date
#             try:
#                 # Find the most recent history record (latest created_at)
#                 appointment_report = AppointmentReportHistory.objects.filter(
#                     user=request.user,
#                     appointment_date=date_obj
#                 ).latest('created_at')  # Get the most recent one
                
#             except AppointmentReportHistory.DoesNotExist:
#                 # If no history record exists, create one
#                 appointment_report = AppointmentReportHistory.objects.create(
#                     user=request.user,
#                     appointment_date=date_obj,
#                     total_pdfs_found=0
#                 )
            
#             # Find the specific PDF file being accessed
#             date_yyyymmdd = date.replace('-', '')
#             base_dir = "E:/TC_BC/Appointments"
#             specific_pdf_pattern = os.path.join(base_dir, f"{date_yyyymmdd}-*", pdf_name)
#             matching_files = glob.glob(specific_pdf_pattern)
            
#             if matching_files and os.path.exists(matching_files[0]):
#                 full_path = matching_files[0]
                
#                 # 🎯 ALWAYS CREATE PDF ACCESS RECORD linked to most recent history
#                 AppointmentReportPDFAccess.objects.create(
#                     appointment_report=appointment_report,  # Link to most recent history record
#                     pdf_name=pdf_name,
#                     pdf_path=full_path.replace('\\', '/')
#                 )
                
#                 logger.info(f"Appointment PDF accessed: {pdf_name} for {date} by {request.user.username} - Linked to history ID {appointment_report.appointment_report_id}")
                
#                 # Serve the PDF file
#                 response = FileResponse(open(full_path, "rb"), content_type="application/pdf")
#                 response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
#                 response['Content-Disposition'] = f'inline; filename="{pdf_name}"'
#                 return response
#             else:
#                 logger.error(f"Appointment PDF file not found: {specific_pdf_pattern}")
#                 raise Http404("PDF file not found")
                
#         except Exception as e:
#             logger.error(f"Error in appointment_report_pdf_access: {str(e)}")
#             import traceback
#             traceback.print_exc()
#             raise Http404("Error accessing PDF")
    
#     return JsonResponse({'success': False, 'error': 'Invalid request method'})

# 🎯 KEEP the original secure_pdf_view as fallback
@login_required
def secure_pdf_view(request, path):
    """Fallback PDF view"""
    file_path = os.path.join(settings.MEDIA_ROOT, "Reports", path.replace('/', os.sep))
    if not os.path.exists(file_path):
        raise Http404("PDF not found")

    response = FileResponse(open(file_path, "rb"), content_type="application/pdf")
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response
