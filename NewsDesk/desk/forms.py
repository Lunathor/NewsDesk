from django import forms
from django.forms import inlineformset_factory

from .models import Post, Image, Video, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'title',
            'text',
            'category',
        ]


class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = '__all__'


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = '__all__'


ImageFormSet = inlineformset_factory(
    Post, Image, form=ImageForm,
    extra=1, can_delete=True, can_delete_extra=True, max_num=10
)

VideoFormSet = inlineformset_factory(
    Post, Video, form=VideoForm,
    extra=1, can_delete=True, can_delete_extra=True, max_num=3,
)
