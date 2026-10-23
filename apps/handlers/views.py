from django.shortcuts import render

# Create your views here.

def handler404(request, exception):
    return render(request, 'Error/404.html', status=404)

# Define 500 Page handler to customized html pages


def handler500(request):
    return render(request, 'Error/500.html', status=500)
