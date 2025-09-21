from django import template

register = template.Library()

@register.filter
def getcrumbs(path):
    return path.split("/")

@register.filter
def getcrumbs(path):
    if not path:  # Ensure path is not None or empty
        return []
    return path.strip('/').split('/')