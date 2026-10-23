from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.template import Library
from django.utils.safestring import mark_safe
from math import ceil
from django.forms import BoundField
import json

register = Library()

# Jsonify any Django ORM Object

@register.filter
def add_input_id(field, id_value):
    """
    Adds a custom ID to a form field.
    """
    if isinstance(field, BoundField):
        field.field.widget.attrs['id'] = id_value
    return field

@register.filter(is_safe=True)
def jsonify(object):
    data = {}
    for msg in object:
        if data.get(msg.tags) is None:
            data[msg.tags] = [msg.message]
        else:
            data[msg.tags].append(msg.message)
    return json.dumps(data)


@register.filter
def divide(value, arg):
    try:
        return int(value) / int(arg)
    except (ValueError, ZeroDivisionError):
        return None


@register.filter
def multiply(value, arg):
    try:
        return int(value)*int(arg)
    except (ValueError, ZeroDivisionError):
        return None


@register.filter
def percentage(value, arg):
    try:
        return round((float(arg)/float(value))*100, 2)
    except (ValueError, ZeroDivisionError):
        return None


@register.filter
def roundbybase(value, base=10):
    return base * round(ceil(value/base))


@register.filter
def dictitem(dictionary, key):
    return dictionary.get(key)

@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)

@register.filter(is_safe=True)
def js(obj):
    return mark_safe(json.dumps(obj))