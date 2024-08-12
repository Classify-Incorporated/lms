from django import template

register = template.Library()

@register.filter
def has_perm(user, perm_name):
    has_permission = user.has_perm(perm_name)
    if has_permission:
        print(f"User '{user.username}' **has** permission: {perm_name}")
    else:
        print(f"User '{user.username}' **does not have** permission: {perm_name}")
    return has_permission
