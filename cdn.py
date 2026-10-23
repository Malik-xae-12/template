import requests
import os
from pathlib import Path

# List of CDN links (corrected SweetAlert2 URL)
cdn_links = [
    "https://cdn.jsdelivr.net/npm/bs-stepper/dist/css/bs-stepper.min.css",
    "https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.css",
    "https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.js",
    "https://cdn.datatables.net/1.10.25/css/jquery.dataTables.min.css",
    "https://cdn.datatables.net/1.10.25/js/jquery.dataTables.min.js",
    "https://code.jquery.com/jquery-3.6.1.min.js",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js",
    "https://cdn.jsdelivr.net/npm/bootstrap-select@1.14.0-beta3/dist/js/bootstrap-select.min.js",
    "https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.min.js",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css",
    "https://cdn.jsdelivr.net/npm/bootstrap-select@1.14.0-beta3/dist/css/bootstrap-select.min.css",
]

# Directory to save files (matches STATICFILES_DIRS)
output_dir = Path("staticfiles/vendor")
output_dir.mkdir(parents=True, exist_ok=True)

for url in cdn_links:
    try:
        # Get the file name from the URL
        file_name = url.split("/")[-1]
        if not file_name or file_name == "61ec39fd2b.js":
            file_name = url.split("/")[-2] + ".js"  # Handle Font Awesome or similar
        file_path = output_dir / file_name

        # Download the file
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"Downloaded: {file_name}")
        else:
            print(f"Failed to download: {url} (Status: {response.status_code})")
    except Exception as e:
        print(f"Error downloading {url}: {e}")