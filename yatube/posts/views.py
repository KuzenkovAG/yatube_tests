from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .forms import PostForm
from .models import Group, Post
from .utils import create_paginator

POST_LIMIT: int = 10


def owner_only(func):
    """Check post owner."""
    def check_owner(request, post_id, *args, **kwargs):
        author = request.user
        post = author.posts.filter(id__exact=post_id)
        if post:
            return func(request, post_id, *args, **kwargs)
        return redirect(reverse_lazy('posts:post_detail', args=[post_id]))
    return check_owner


def index(request):
    """Main page."""
    template = 'posts/index.html'
    posts_list = Post.objects.select_related('author', 'group').all()
    page_obj = create_paginator(request, posts_list, POST_LIMIT)

    return render(request, template, {'page_obj': page_obj})


def group_post(request, slug):
    """Page of group."""
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts.all()
    page_obj = create_paginator(request, posts_list, POST_LIMIT)

    template = 'posts/group_list.html'

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    """Page of user profile."""
    User = get_user_model()

    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    post_count = posts.count()
    page_obj = create_paginator(request, posts, POST_LIMIT)

    context = {
        'page_obj': page_obj,
        'post_count': post_count,
        'author': author,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Page of post detail."""
    post = get_object_or_404(Post, id=post_id)
    post_count = Post.objects.select_related('author', 'group').filter(
        author__exact=post.author).count()

    context = {
        'post': post,
        'post_count': post_count,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Page for create new post."""
    title = 'Новый пост'
    form = PostForm(request.POST or None)
    template = 'posts/create_post.html'
    if request.method == 'POST':
        if form.is_valid():
            user = request.user
            form = form.save(commit=False)
            form.author = user
            form.save()
            return redirect(reverse_lazy(
                'posts:profile',
                args=[user.username]
            ))
    return render(request, template, {'form': form, 'title': title})


@login_required
@owner_only
def post_edit(request, post_id):
    """Page of edit post."""
    title = 'Редактировать пост'

    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None, instance=post)
    template = 'posts/create_post.html'

    if request.method == 'POST':
        if form.is_valid():
            post.save()
            return redirect(reverse_lazy('posts:post_detail', args=[post_id]))
    return render(request, template, {
        'form': form,
        'title': title,
        'is_edit': True,
    })
