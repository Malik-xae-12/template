from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from apps.helpers.threads import EmailThread
from .models import Profile
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.db.models import Q

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(
            user=instance)
        profile.avatar = profile.get_default_avatar()
        profile.save()
        # new_pass = User.objects.make_random_password()
        instance.set_password('Temp@123')
        instance.save()
        domain = Site.objects.get_current().domain
        msg_html = render_to_string('auth/emails/userinfo.html',
                                    {'user': instance, 'password': 'Temp@123', 'domain': domain})

        datatuple = (instance.username, '', msg_html, None, [instance.email])
        # EmailThread(messages=(datatuple,), mode='bulk').start()