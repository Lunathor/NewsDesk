from django.shortcuts import render, redirect
from django.views.generic import ListView
from .models import Post, Comment
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
