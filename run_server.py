
from waitress import serve

from root.wsgi import application
# documentation: https://docs.pylonsproject.org/projects/waitress/en/stable/api.html

if __name__ == '__main__':
    print("server running")
    serve(application, host = '0.0.0.0', port=8080)