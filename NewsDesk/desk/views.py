from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.db.utils import IntegrityError
from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.models import Group
from rest_framework.reverse import reverse_lazy
from urllib3 import request

from .models import Image, Video, Post, User, Comment
from .forms import PostForm, ImageFormSet, VideoFormSet
from .utils import generate_otp, verify_otp, send_email_otp, send_email_new_comment
from .mixins import IsVerifiedMixin, AuthorRequiredMixin, CustomLoginRequiredMixin


# TODO: сделать поиск
class PostListView(ListView):
    model = Post
    ordering = '-time_in'
    template_name = 'posts.html'
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


# TODO: Когда добавлю комменты и посты доработать
class PersonalOfficeView(CustomLoginRequiredMixin, ListView):
    model = Comment
    template_name = 'personal_office.html'
    context_object_name = 'comments'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['posts'] = Post.objects.filter(author=self.request.user).order_by('-time_in')
        
        return context
    
    def post(self, pk, ):
        print(f'        a       {pk}{type(pk)}')
        # obj = Comment.objects.get(id=pk)
        # if confirm:
        #     obj.confirmed = True
        # else:
        #     obj.delete()
        
        return redirect('personal')


def logout_view(request):
    logout(request)
    return redirect('/post/')


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        try:
            news = request.POST['news_subscription']
            news_subscription = True
        except KeyError:
            news_subscription = False
        
        if password1 == password2:
            try:
                user = User.objects.create_user(
                    username=username, email=email, password=password1, news_subscription=news_subscription
                )
            except IntegrityError:
                error_msg = 'Пользователь с таким именем уже существует'
                return render(request, 'registration/register.html', {'msg': error_msg})
            
            generate_otp(user=user)
            send_email_otp(user=user)
            
            return redirect('verify_otp', user_id=user.id)
        
        else:
            error_msg = 'Проверьте правильность написания паролей'
            return render(request, 'registration/register.html', {'msg': error_msg})
    
    return render(request, 'registration/register.html')


def verify(request, user_id=None):
    user = User.objects.get(id=user_id)
    
    if request.method == 'POST':
        email_otp = request.POST['email_otp']
        
        if verify_otp(otp=email_otp, user=user):
            user.is_verified = True
            user.email_otp = None
            
            logged_users = Group.objects.get(name='logged_users')
            user.groups.add(logged_users)
            
            user.save()
            login(request, user)
            
            return redirect('/post/')
        else:
            msg = 'Пожалуйста проверьте правильность написания кода'
            return render(request, 'registration/verify_otp.html', {'error': msg, 'user': user})
    
    return render(request, 'registration/verify_otp.html', {'user': user})


@login_required
def repeat_verify(request):
    user = request.user
    
    generate_otp(user=user)
    send_email_otp(user=user)
    
    return redirect('verify_otp', user_id=user.id)
