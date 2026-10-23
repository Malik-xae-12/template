"""root URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.admindocs import urls as admindocs_urls
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.views.static import serve
from django.http import HttpResponse, Http404
import os
import mimetypes

def serve_static_with_correct_mimetype(request, path):
    """Custom view to serve static files with correct MIME type"""
    if settings.STATICFILES_DIRS:
        static_root = settings.STATICFILES_DIRS[0]
    else:
        static_root = settings.STATIC_ROOT
        
    file_path = os.path.join(static_root, path)
    
    # Security check
    if not os.path.abspath(file_path).startswith(os.path.abspath(static_root)):
        raise Http404("File not found")
    
    if not os.path.exists(file_path):
        raise Http404("File not found")
    
    # Determine content type
    if file_path.endswith('.mjs'):
        content_type = 'application/javascript'
    else:
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'
    
    try:
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response['Cache-Control'] = 'public, max-age=31536000'
            if file_path.endswith(('.mjs', '.js')):
                response['X-Content-Type-Options'] = 'nosniff'
            return response
    except IOError:
        raise Http404("File not found")

urlpatterns = [
    path('auth/', include('apps.accounts.urls')),
    path('', include('apps.base.urls')),
    path('profile/', include('apps.profile.urls')),
    path("i18n/", include("django.conf.urls.i18n")),
    # django-admin:
    path('admin/docs/', include(admindocs_urls)),
    path('admin/', admin.site.urls),
    path("files/", include("apps.medfiles.urls")),
    path('accounts/', include('allauth.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Custom static file serving with proper MIME types
    urlpatterns += [
        path('static/<path:path>', serve_static_with_correct_mimetype, name='serve_static_files'),
    ]

handler404 = "apps.handlers.views.handler404"
handler500 = "apps.handlers.views.handler500"