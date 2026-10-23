import os

def get_appointment_report_path(appointments_dir, input_date_str):
    """
    Locate all DailyAppt-KH.pdf appointment reports for a given date.
    Returns a list of tuples: (folder_path, pdf_path, pdf_filename)
    """
    if not os.path.isdir(appointments_dir):
        return []

    matching_folders = [
        f for f in os.listdir(appointments_dir)
        if os.path.isdir(os.path.join(appointments_dir, f)) and f.startswith(input_date_str + "-")
    ]

    report_paths = []
    for folder in sorted(matching_folders, reverse=True):
        folder_path = os.path.join(appointments_dir, folder)
        candidate_pdf_path = os.path.join(folder_path, "DailyAppt-KH.pdf")
        if os.path.exists(candidate_pdf_path):
            relative_folder = os.path.relpath(folder_path, 'E:/TC_BC').replace('\\', '/')
            relative_pdf = os.path.relpath(candidate_pdf_path, 'E:/TC_BC').replace('\\', '/')
            report_paths.append((relative_folder, relative_pdf, "DailyAppt-KH.pdf"))

    return report_paths


def get_patient_report_path(reports_root_dir, input_date_str, patient_identifier):
    """
    Find all patient folders for a given date and collect available PDF paths.

    Returns a list of tuples:
    (relative_folder_path, pdf_relative_path, pdf_filename)
    """
    formatted_date = input_date_str
    report_paths = []
    
    for root, dirs, files in os.walk(reports_root_dir):
        current_dir_name = os.path.basename(root)
        if current_dir_name.startswith(formatted_date + "-"):
            patient_folder_path = os.path.join(root, patient_identifier)
            if os.path.isdir(patient_folder_path):
                relative_path = os.path.relpath(patient_folder_path, reports_root_dir).replace('\\', '/')
                
                for pdf_name in ['DrugAdmin.pdf', 'EPR.pdf']:
                    pdf_path = os.path.join(patient_folder_path, pdf_name)
                    if os.path.exists(pdf_path):
                        pdf_relative = os.path.relpath(pdf_path, 'E:/TC_BC').replace('\\', '/')
                        report_paths.append((relative_path, pdf_relative, pdf_name))
    
    return report_paths
