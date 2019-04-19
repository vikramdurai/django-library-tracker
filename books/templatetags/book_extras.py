from django import template
from books.forms import UserJoinApproveForm
register = template.Library()


@register.simple_tag
def get_form(theo):
    return UserJoinApproveForm({'id': theo})
