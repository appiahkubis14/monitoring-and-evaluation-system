# monitoring/templatetags/monitoring_filters.py
from django import template
from django.utils import timezone
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def filter_overdue(compliance_checks):
    today = timezone.now().date()
    return [check for check in compliance_checks if check.due_date < today and check.status == 'pending']

@register.filter
def filter_active(projects):
    return [project for project in projects if project.status == 'active']

@register.filter
def map_attr(items, attr_name):
    return [getattr(item, attr_name) for item in items]





# monitoring/templatetags/monitoring_filters.py
from django import template
from django.utils import timezone
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def filter_overdue(compliance_checks):
    """Filter compliance checks that are overdue"""
    today = timezone.now().date()
    return [check for check in compliance_checks if check.due_date < today and check.status == 'pending']

@register.filter
def filter_status(queryset, status):
    """Filter queryset by status"""
    return queryset.filter(status=status)

@register.filter
def intcomma(value):
    """Format numbers with commas"""
    if value is None:
        return ""
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return str(value)

@register.filter
def timeuntil(value):
    """Custom timeuntil filter"""
    if not value:
        return ""
    
    today = timezone.now().date()
    if isinstance(value, datetime):
        value = value.date()
    
    delta = value - today
    
    if delta.days == 0:
        return "Today"
    elif delta.days == 1:
        return "Tomorrow"
    elif delta.days == -1:
        return "Yesterday"
    elif delta.days > 0:
        return f"In {delta.days} days"
    else:
        return f"{abs(delta.days)} days ago"

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary"""
    return dictionary.get(key)

@register.filter
def multiply(value, arg):
    """Multiply value by argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divide value by argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0