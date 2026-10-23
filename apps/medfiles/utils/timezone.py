# utils/timezone.py
from django.utils import timezone
import pytz

DUBAI_TZ = pytz.timezone("Asia/Dubai")

def now_dubai():
    """Return current timezone-aware datetime in Dubai time"""
    return timezone.now().astimezone(DUBAI_TZ)
