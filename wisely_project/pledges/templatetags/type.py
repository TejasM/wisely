from django import template

from pledges.models import Pledge


register = template.Library()


@register.filter('pledgeType')
def pledgeType(obj):
    if not obj:
        return False
    return obj is Pledge