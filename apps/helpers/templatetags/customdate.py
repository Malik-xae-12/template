from django import template
import arrow

register = template.Library()


# Humanize Datetime
@register.filter
def humanize(value):
    return arrow.get(value).humanize()
