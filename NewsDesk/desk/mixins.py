from django.contrib.auth.mixins import AccessMixin
from django.contrib import messages
from django.shortcuts import redirect


class AuthorRequiredMixin(AccessMixin):

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_staff:
            if not user.is_authenticated:
                return self.handle_no_permission()
            if not user.is_verified:
                return self.handle_no_permission()

            if user != self.get_object().author:
                messages.info(request, 'Вы не являетесь автором')
                return redirect('PostList')
        return super().dispatch(request, *args, **kwargs)


class IsVerifiedMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_staff:
            if not user.is_authenticated:
                return self.handle_no_permission()

            if not user.is_verified:
                messages.info(
                    request,
                    '''Доступно только верифицированным пользователям,
                    для верификации пройдите в Личный кабинет/Верификация'''
                )
                return redirect('PostList')
        return super().dispatch(request, *args, **kwargs)


class CustomLoginRequiredMixin(AccessMixin):
    """ Кастомный миксин для редиректа пользователей, которые не вошли на сайт"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)