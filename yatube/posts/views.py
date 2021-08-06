from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.core.cache import cache
from django.views.decorators.http import require_GET

from .forms import PostForm, CommentForm
from .models import Comment, Follow, Group, Post, User


@require_GET
def index(request):
    post_list = cache.get("index_page")
    if not post_list:
        post_list = Post.objects.all()
        cache.set("index_page", post_list)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "index.html",
        {"page": page, }
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.group_posts.all()
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "group.html", {"group": group, "page": page})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.author_posts.all()
    post_amt = posts.count()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        if Follow.objects.filter(user=request.user, author=author).exists():
            following = True
    context = {"author": author,
               "post_amt": post_amt,
               "page": page,
               "following": following,
               }
    return render(request, "profile.html", context)


@login_required()
def post_view(request, username, post_id):
    post_of_author = get_object_or_404(
        Post,
        author__username=username,
        pk=post_id
    )
    author = post_of_author.author
    post_amt = author.author_posts.count()
    comments = Comment.objects.filter(post=post_of_author)
    form = CommentForm()
    context = {
        "author": author,
        "post_of_author": post_of_author,
        "post_amt": post_amt,
        "comments": comments,
        "form": form,
    }
    return render(request, "post.html", context)


@login_required()
def new_post(request):
    header = "Добавить запись"
    action = "Добавить"
    form = PostForm(request.POST or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect("index")
    return render(
        request,
        "new.html",
        {"form": form, "header": header, "action": action}
    )


@login_required()
def post_edit(request, username, post_id):
    header = "Редактировать запись"
    action = "Сохранить"
    profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=profile)
    if request.user != profile:
        return redirect("post", username=username, post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("post", username=request.user.username, post_id=post_id)

    context = {
        "form": form, "post": post, "header": header, "action": action,
        "post_id": post_id, "username": username,
    }
    return render(request, "new.html", context)


@login_required()
def add_comment(request, username, post_id):
    post_of_author = get_object_or_404(
        Post,
        author__username=username,
        pk=post_id
    )
    if request.method == "POST":
        form = CommentForm(request.POST or None)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.author = request.user
            new_comment.post = post_of_author
            new_comment.save()
            return redirect("post", post_of_author.author.username, post_id)
        return render(
            request,
            "includes/comments.html",
            {"form": form}
        )
    form = CommentForm()
    return render(request, "includes/comments.html", {"form": form})


@login_required
def follow_index(request):
    follow = Follow.objects.filter(user=request.user)
    post_list = Post.objects.filter(author__username=follow.author.username)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "follow.html",
        {"page": page, },
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = get_object_or_404(User, username=request.user)
    if not Follow.objects.filter(author=author, user=user).exists():
        Follow.objects.create(user_id=user.id, author_id=author.id)
    return redirect("profile", username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = get_object_or_404(User, username=request.user)
    Follow.objects.filter(user=user, author=author).delete()
    return redirect("profile", username)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
