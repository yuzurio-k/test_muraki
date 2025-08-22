from django import template
from urllib.parse import urlencode

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """辞書から値を取得するフィルター"""
    return dictionary.get(key, 0)

@register.filter
def div(value, arg):
    """割り算フィルター"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """掛け算フィルター"""
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0

@register.filter
def max_value(dictionary):
    """辞書の最大値を取得"""
    if dictionary:
        return max(dictionary.values())
    return 0

@register.simple_tag
def url_params(request, **kwargs):
    """現在のクエリパラメータを保持してURLを生成"""
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value:
            params[key] = value
        elif key in params:
            del params[key]
    return '?' + urlencode(params) if params else ''

@register.filter
def japanese_full_name(user):
    """日本語の姓名表示（姓 名の順序）"""
    if user.last_name and user.first_name:
        return f"{user.last_name} {user.first_name}"
    elif user.last_name:
        return user.last_name
    elif user.first_name:
        return user.first_name
    else:
        return user.username
