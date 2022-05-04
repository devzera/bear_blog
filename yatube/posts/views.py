from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utills import get_paginator


@cache_page(20, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.select_related('author', 'group').all()
    page_obj = get_paginator(request, post_list)['page_obj']
    context = {
        'index': True,
        'post_list': post_list,
        'page_obj': page_obj,
    }

    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author', 'group').all()
    page_obj = get_paginator(request, post_list)['page_obj']
    is_group_list = True
    context = {
        'post_list': post_list,
        'group': group,
        'page_obj': page_obj,
        'is_group_list': is_group_list
    }

    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    is_user = False
    following = False

    if str(request.user) == username:
        is_user = True

    user = get_object_or_404(User, username=username)

    follow = Follow.objects.filter(author=user)
    if len(follow) != 0:
        following = True

    post_list = user.posts.select_related('author', 'group').all()
    page_obj = get_paginator(request, post_list)['page_obj']
    count_posts = post_list.count()
    is_profile = True

    context = {
        'post_list': post_list,
        'author': user,
        'count_posts': count_posts,
        'page_obj': page_obj,
        'is_profile': is_profile,
        'is_user': is_user,
        'following': following
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
        'count_posts': count_posts,
        'post': post,
        'comments': comments,
        'form': form
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

    username = request.user
    post = form.save(commit=False)
    post.author = username
    post.save()

    return redirect('posts:profile', username)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = Post.objects.select_related('author', 'group').get(pk=post_id)
    username = request.user
    author = post.author.username

    if author != str(username):
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
    post = Post.objects.select_related('author', 'group').get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):

    username = request.user
    user = User.objects.get(username=username)
    follower = user.follower.all()
    follower = [name.author for name in follower]
    posts = Post.objects.filter(author__username__in=follower)
    page_obj = get_paginator(request, posts)['page_obj']

    context = {
        'follow': True,
        'posts': posts,
        'follower': follower,
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):

    user = get_object_or_404(User, username=request.user)
    author = get_object_or_404(User, username=username)

    follower = user.follower.filter(author=author)

    if str(request.user) == username or len(follower) != 0:
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

    follower = user.follower.filter(author=author)

    if str(request.user) == username or len(follower) == 0:
        return redirect('posts:profile', username=username)

    follow = Follow.objects.get(
        user=user,
        author=author
    )
    follow.delete()

    return redirect('posts:profile', username=username)
