from django import template

register = template.Library()

@register.filter
def duration(td):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 60*60)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f'{hours} hour(s)'
    elif minutes > 0:
        return f'{minutes} minute(s)'
    else:
        return f'{seconds} second(s)'