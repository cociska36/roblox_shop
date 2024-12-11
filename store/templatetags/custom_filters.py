from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)  # Вернуть значение по ключу или 0, если ключ не найден
