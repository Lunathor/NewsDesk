from django import template
from desk.models import Image, Post, Video, Comment, User

register = template.Library()


@register.filter
def preview(value: Post) -> Image:
    """
        Принимает объект модели Post и возвращает первую картинку в этой модели
    """
    img = Image.objects.filter(post=value).first()
    return img.file.url


@register.filter
def image_check(value: Post) -> bool:
    """
        Принимает объект модели Post и проверяет есть ли в нем прикрепленные картинки
    """
    if Image.objects.filter(post=value.id).first():
        return True
    else:
        return False


@register.filter
def video_check(value: Post) -> bool:
    """
        Принимает объект модели Post и проверяет есть ли в нем прикрепленные видео
    """
    if Video.objects.filter(post=value.id).first():
        return True
    else:
        return False


@register.filter
def get_image(value: Post) -> list[Image]:
    """
        Принимает объект модели Post, обрабатывая, возвращает список всех связанных изображений
    """
    return Image.objects.filter(post=value.id).all()


@register.filter
def get_video(value: Post) -> list[Video]:
    """
        Принимает объект модели Post, обрабатывая, возвращает список всех связанных видео
    """
    return Video.objects.filter(post=value.id).all()

@register.filter
def censor_mail(value: User) -> str:
    email = value.email
    before_at = ''
    after_at = ''
    at = False

    for e in email:
        if '@' == e:
            at = True

        if at:
            after_at = after_at + e
        else:
            before_at = before_at + e

    return before_at.replace(before_at[2:], '*' * len(before_at[2:])) + after_at

@register.filter
def have_comments(pk: int) -> bool:
    if Comment.objects.filter(post=pk, confirmed=False).exists():
        return True
    else:
        return False
