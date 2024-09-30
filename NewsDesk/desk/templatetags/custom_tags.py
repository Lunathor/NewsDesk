from django import template

from desk.models import Image


register = template.Library()


@register.simple_tag()
def empty_img():
    """
        Возвращает заготовленную картинку, обозначающую,
    что в посте нет картинок
    """
    img = Image.objects.filter(id=1).get()
    return img.file.url
