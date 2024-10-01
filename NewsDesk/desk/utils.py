from django.conf import settings
from django.core.mail import send_mail
from rest_framework.reverse import reverse_lazy

from desk.models import User, Post


def send_email_new_comment(author: User, post_pk: int) -> None:
    """Отправляет сообщение на почту о том, что под его постов появился новый комментарий"""

    email = author.email
    url = reverse_lazy('personal')
    post = Post.objects.get(pk=post_pk)
    msg_post = post.preview()

    send_mail(
        'Новый комментарий к вашему посту',
        f'''К вашему посту: {msg_post} отправили комментарий.
        Для того, чтобы комментарий увидели другие пользователи, его нужно утвердить в личном кабинете: {url}''',
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )