from django import template

register = template.Library()

@register.inclusion_tag('main_app/dark_mode_toggle.html')
def dark_mode_toggle():
    """
    Template tag to include the dark mode toggle button.
    Returns the context needed for the dark mode toggle template.
    """
    return {
        'dark_mode_icon': 'fa-moon',  # Default icon
        'dark_mode_text': 'Toggle Dark Mode'
    } 