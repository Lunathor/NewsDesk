from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic import ListView, DeleteView, UpdateView, CreateView
from rest_framework.reverse import reverse_lazy

from .forms import ImageFormSet, VideoFormSet, PostForm
from .mixins import AuthorRequiredMixin, IsVerifiedMixin
from .models import Post, Comment, Image, Video
from .utils import send_email_new_comment


class PostListView(ListView):
    model = Post
    ordering = '-time_in'
    template_name = 'post_listview.html'
    context_object_name = 'post'
    paginate_by = 12


def post_detail(request, pk):
    post = Post.objects.get(pk=pk)
    comments = Comment.objects.filter(post=post).order_by('-time_in')
    if request.user.is_authenticated:
        user_verification = request.user.is_verified or request.user.is_staff
    else:
        user_verification = False
    
    if request.method == 'POST':
        text = request.POST['text']
        Comment.objects.create(text=text, post=post, author=request.user)
        
        send_email_new_comment(author=post.author, post_pk=post.id)
        
        return redirect('PostDetail', pk=pk)
    
    return render(
        request,
        'post.html',
        {'post': post, 'comments': comments, 'user_verification': user_verification}
    )


class PostInline():
    form_class = PostForm
    model = Post
    template_name = "post_create_or_update.html"

    def form_valid(self, form):
        named_formsets = self.get_named_formsets()
        if not all((x.is_valid() for x in named_formsets.values())):
            return self.render_to_response(self.get_context_data(form=form))

        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()

        # для каждого набора форм попытаться найти определенную функцию
        # сохранения набора форм, в противном случае просто сохранить
        for name, formset in named_formsets.items():
            formset_save_func = getattr(self, 'formset_{0}_valid'.format(name), None)
            if formset_save_func is not None:
                formset_save_func(formset)
            else:
                formset.save()
        return redirect('PostList')

    def formset_video_valid(self, formset):
        """
            Триггер для сохранения формсета видео.
        """
        video = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for vid in video:
            vid.post = self.object
            vid.save()

    def formset_images_valid(self, formset):
        """
            Триггер для сохранения формсета изображений.
        """
        images = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for image in images:
            image.post = self.object
            image.save()


class PostCreateView(IsVerifiedMixin, PostInline, CreateView):

    def get_context_data(self, **kwargs):
        ctx = super(PostCreateView, self).get_context_data(**kwargs)
        ctx['named_formsets'] = self.get_named_formsets()
        return ctx

    def get_named_formsets(self):
        if self.request.method == "GET":
            return {
                'video': VideoFormSet(prefix='video'),
                'images': ImageFormSet(prefix='images'),
            }
        else:
            return {
                'video': VideoFormSet(self.request.POST or None, self.request.FILES or None, prefix='video'),
                'images': ImageFormSet(self.request.POST or None, self.request.FILES or None, prefix='images')
            }


class PostUpdateView(AuthorRequiredMixin, PostInline, UpdateView):

    def get_context_data(self, **kwargs):
        ctx = super(PostUpdateView, self).get_context_data(**kwargs)
        ctx['named_formsets'] = self.get_named_formsets()
        return ctx

    def get_named_formsets(self):
        return {
            'video': VideoFormSet(
                self.request.POST or None,
                self.request.FILES or None,
                instance=self.object,
                prefix='videos'
            ),

            'images': ImageFormSet(
                self.request.POST or None,
                self.request.FILES or None,
                instance=self.object,
                prefix='images'
            ),
        }


class PostDeleteView(AuthorRequiredMixin, DeleteView):
    model = Post
    template_name = 'post_delete.html'
    success_url = reverse_lazy('PostList', )


def delete_image(request, pk):
    try:
        image = Image.objects.get(id=pk)
    except Image.DoesNotExist:
        messages.success(
            request, 'Изображение не найдено'
            )
        return redirect('post_update', pk=image.post.id)

    image.delete()
    messages.success(
            request, 'Изображение удаленно'
            )
    return redirect('post_update', pk=image.post.id)


def delete_video(request, pk):
    try:
        video = Video.objects.get(id=pk)
    except Video.DoesNotExist:
        messages.success(
            request, 'Видео не найдено'
            )
        return redirect('post_update', pk=video.post.id)

    video.delete()
    messages.success(
            request, 'Видео удалено'
            )
    return redirect('post_update', pk=video.post.id)
