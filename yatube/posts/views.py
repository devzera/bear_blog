from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from yatube.settings import CACHE_SAVE_TIME

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utills import get_paginator


@cache_page(timeout=CACHE_SAVE_TIME, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'

    post_list = Post.objects.select_related('author', 'group').all()
    page_obj = get_paginator(request, post_list)['page_obj']

    context = {
        'post_list': post_list,
        'page_obj': page_obj,
        'index': True
    }

    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'

    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author', 'group').all()
    page_obj = get_paginator(request, post_list)['page_obj']

    context = {
        'post_list': post_list,
        'page_obj': page_obj,
        'group': group,
        'is_group_list': True
    }

    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'

    user = get_object_or_404(User, username=username)
    following = Follow.objects.filter(author=user).exists()
    post_list = user.posts.select_related('author', 'group').all()
    page_obj = get_paginator(request, post_list)['page_obj']

    count_posts = post_list.count()
    is_user = request.user.username == username

    context = {
        'post_list': post_list,
        'page_obj': page_obj,
        'author': user,
        'following': following,
        'count_posts': count_posts,
        'is_user': is_user,
        'is_profile': True
    }

    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'

    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.select_related(
        'author',
        'post'
    ).filter(
        post__pk=post_id
    )

    count_posts = Post.objects.select_related(
        'author',
        'group'
    ).filter(
        author__username=post.author.username
    ).count()

    context = {
        'post': post,
        'comments': comments,
        'form': form,
        'count_posts': count_posts
    }

    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'

    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )

    if not form.is_valid():
        return render(request, template, {'form': form})

    post = form.save(commit=False)
    post.author = request.user
    post.save()

    return redirect('posts:profile', request.user)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'

    post = get_object_or_404(Post, pk=post_id)

    if post.author.username != request.user.username:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if not form.is_valid():
        return render(
            request,
            template,
            {'form': form, 'is_edit': True, 'post': post}
        )

    form.save()

    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = get_paginator(request, posts)['page_obj']

    context = {
        'follow': True,
        'posts': posts,
        'page_obj': page_obj
    }

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):

    user = get_object_or_404(User, username=request.user)
    author = get_object_or_404(User, username=username)

    follower = user.follower.filter(author=author).exists()

    if request.user.username == username or follower:
        return redirect('posts:profile', username=username)

    Follow.objects.create(
        user=user,
        author=author
    )

    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):

    user = get_object_or_404(User, username=request.user)
    author = get_object_or_404(User, username=username)

    follower = user.follower.filter(author=author).exists()

    if request.user.username == username or not follower:
        return redirect('posts:profile', username=username)

    follow = get_object_or_404(
        Follow,
        user=user,
        author=author
    )
    follow.delete()

    return redirect('posts:profile', username=username)
