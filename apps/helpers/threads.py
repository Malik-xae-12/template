# from django.core.mail import EmailMessage
# from django.conf import settings
# import threading


# from apps.helpers.utils import send_mass_html_mail


# class EmailThread(threading.Thread):
#     def __init__(self, to=None, subject=None, body=None, file=None, messages=None, mode='single', cc=None, **kwargs):
#         self.mode = mode
#         self.to = to
#         self.cc = settings.DEFAULT_CC_EMAIL if cc is None else cc
#         self.attachment = file
#         self.subject = subject
#         self.body = body
#         self.messages = messages
#         super(EmailThread, self).__init__(**kwargs)

#     def run(self):
#         if self.mode == 'single':
#             email = EmailMessage(
#                 self.subject, self.body, '', self.to, cc=self.cc)
#             if self.attachment is not None:
#                 email.attach(f'{self.subject}.pdf', self.attachment.read())
#             email.content_subtype = "html"  # this is the crucial part
#             email.send(fail_silently=True)
#         else:
#             send_mass_html_mail(self.messages, fail_silently=False, cc=self.cc)
