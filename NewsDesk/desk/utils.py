import pyotp
from django.conf import settings
from django.core.mail import send_mail
from rest_framework.reverse import reverse_lazy

from .models import User, Post


def generate_otp(user: User) -> str:
    """
        Функция генерирует одноразовый код на основе библиотеки pyotp.
    И присваивает этот код в поле email_otp к пользователю, для которого
    этот код был сгенерирован.
    """
    
    totp = pyotp.TOTP(pyotp.random_base32(), interval=300)
    user.email_otp = totp.now()
    user.save()
    
    return totp.now()


def verify_otp(otp: str, user: User) -> bool:
    """
        Сверяет данные одноразового кода который ввел пользователь.
    С тем, который на самом деле привязан к пользователю.
    """
    
    return otp == user.email_otp


def send_email_otp(user: User) -> None:
    """Отправляет сообщение на почту с кодом подтверждения."""
    
    email = user.email
    email_otp = user.email_otp
    
    send_mail(
        'Подтверждение почты с помощью одноразового кода',
        f'Ваш код подтверждения для регистрации на сайте: {email_otp}',
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )


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


def do_newsletter(msg_title: str, msg_text: str) -> None:
    """ Функция, которая делает рассылку всем пользователям, подписанным на новостную рассылку"""
    
    for user in User.objects.filter(news_subscription=True):
        email = user.email
        print(email)
        
        send_mail(
            msg_title,
            msg_text,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
