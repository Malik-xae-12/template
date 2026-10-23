# from django.db.models.signals import post_save, pre_delete, m2m_changed
# from django.contrib.auth.signals import user_logged_in, user_login_failed
# from django.contrib.auth.models import User
# from django.dispatch import receiver
# from apps.helpers.threads import EmailThread
# from apps.helpers.utils import get_client_ip, send_mass_html_mail
# from django.template.loader import render_to_string
# from django.contrib.sites.models import Site
# from django.db.models import Q
# import requests
# from user_agents import parse


# @receiver(user_login_failed)
# def user_login_attempt(request, credentials, **kwargs):
#     username = credentials.get('username')
#     if User.objects.filter(Q(username=username) | Q(email=username)):
#         user = User.objects.get(Q(username=username) | Q(email=username))
#         if user.email:
#             client_ip = get_client_ip(request)
#             ua_string = request.META.get('HTTP_USER_AGENT')
#             if ua_string is not None:
#                 user_agent = parse(ua_string)
#                 os = user_agent.os.family
#                 device = user_agent.device.family
#                 browser = user_agent.browser.family
#             else:
#                 os, device, browser = "Not Detected", "Not Detected", "Not Detected"

#             ip_resp = requests.get(f'http://ip-api.com/json/{client_ip}')
#             if ip_resp.json()['status'] == 'fail':
#                 ip_location_info = "Location Not Found"
#             else:
#                 resp_data = ip_resp.json()
#                 ip_location_info = f"{resp_data.get('city','')}, {resp_data.get('regionName','')}, {resp_data.get('country','')}"
#             emailbody = render_to_string('auth/emails/loginattempt.html',
#                                          {'user': user, 'context': {'ip': client_ip, 'location': ip_location_info, 'os': os, 'device': device, 'browser': browser}})
#             subject = f"Login Attempt - {user.username}"
#             EmailThread(to=[user.email], subject=subject,
#                         body=emailbody).start()


# @receiver(user_logged_in)
# def user_login(request, user, **kwargs):
#     user_email = user.email
#     if user_email:
#         client_ip = get_client_ip(request)
#         ua_string = request.META.get('HTTP_USER_AGENT')
#         if ua_string is not None:
#             user_agent = parse(ua_string)
#             os = user_agent.os.family
#             device = user_agent.device.family
#             browser = user_agent.browser.family
#         else:
#             os, device, browser = "Not Detected", "Not Detected", "Not Detected"
#         ip_resp = requests.get(f'http://ip-api.com/json/{client_ip}')
#         if ip_resp.json()['status'] == 'fail':
#             ip_location_info = "Location Not Found"
#         else:
#             resp_data = ip_resp.json()
#             ip_location_info = f"{resp_data.get('city','')}, {resp_data.get('regionName','')}, {resp_data.get('country','')}"
#         emailbody = render_to_string('auth/emails/logininfo.html',
#                                      {'user': user, 'context': {'ip': client_ip, 'location': ip_location_info, 'os': os, 'device': device, 'browser': browser}})
#         subject = f"Login Successfull - {user.username}"
#         EmailThread(to=[user_email], subject=subject,
#                     body=emailbody).start()

