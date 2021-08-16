from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from urllib.parse import quote

from .. models import Comment, Follow, Group, Post

User = get_user_model()


class GroupURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Test-title",
            description="Test_description",
            slug="test-slug",
        )
        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=User.objects.create_user(username="test_author"),
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = GroupURLTests.post.author
        self.not_author = User.objects.create_user(username="not_author")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            reverse("index"): "index.html",
            reverse("group", kwargs={
                "slug": GroupURLTests.group.slug}): "group.html",
            reverse("new_post"): "new.html",
            reverse("profile", kwargs={
                "username": self.user}): "profile.html",
            reverse("post", kwargs={
                "username": self.user,
                "post_id": GroupURLTests.post.pk
            }): "post.html",
            reverse("edit", kwargs={
                "username": self.user,
                "post_id": GroupURLTests.post.pk
            }): "new.html",
            "leo/": "misc/404.html",
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.not_author_client.get(adress)
                if adress != "/test_author/1/edit/":
                    self.assertTemplateUsed(response, template)

        for adress in templates_url_names.keys():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                if adress == "leo/":
                    self.assertEqual(response.status_code, 404)
                else:
                    self.assertEqual(response.status_code, 200)

        for adress in templates_url_names.keys():
            with self.subTest(adress=adress):
                response = self.not_author_client.get(adress)
                if adress == "/test_author/1/edit/":
                    self.assertEqual(response.status_code, 302)
                elif adress == "leo/":
                    self.assertEqual(response.status_code, 404)
                else:
                    self.assertEqual(response.status_code, 200)

    def test_post_edit_url_redirect_anonymous(self):
        """Страница /<username>/<post_id>/edit/ перенаправляет
        анонимного пользователя."""
        response = self.guest_client.get(
            "/test_author/1/edit/",
            follow=True
        )
        self.assertRedirects(
            response,
            "/auth/login/?next=/test_author/1/edit/"
        )

    def test_add_comment_url_redirect_anonymous(self):
        form_data = {
            "post": GroupURLTests.post.pk,
            "author": GroupURLTests.post.author,
            "text": "Second comment",
        }
        response = self.guest_client.post(
            reverse("add_comment", kwargs={
                "username": self.user,
                "post_id": GroupURLTests.post.pk
            }),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse(
            "login"
        ) + "?next=" + quote(reverse(
            "add_comment", kwargs={
                "username": self.user,
                "post_id": GroupURLTests.post.pk
            }), ""))
        self.assertEqual(Comment.objects.count(), 0)

    def test_profile_follow_url_authorized_client(self):
        response = self.not_author_client.get(
            reverse(
                "profile_follow", kwargs={
                    "username": GroupURLTests.post.author,
                }
            ), follow=True)
        self.assertRedirects(response, reverse("profile", kwargs={
                "username": self.user}))
        self.assertEqual(Follow.objects.count(), 1)

    def test_profile_unfollow_url_authorized_client(self):
        Follow.objects.create(
            user=self.not_author,
            author=GroupURLTests.post.author
        )
        response = self.not_author_client.get(
            reverse(
                "profile_unfollow", kwargs={
                    "username": GroupURLTests.post.author,
                }
            ), follow=True)
        self.assertRedirects(response, reverse("profile", kwargs={
                "username": GroupURLTests.post.author}))
        self.assertEqual(Follow.objects.count(), 0)

    def test_profile_follow_url_redirect_anonymous(self):
        response = self.guest_client.get(
            reverse(
                "profile_follow", kwargs={
                    "username": GroupURLTests.post.author,
                }
            ), follow=True)
        self.assertRedirects(response, reverse(
            "login"
        ) + "?next=" + quote(reverse(
            "profile_follow", kwargs={
                "username": GroupURLTests.post.author,
            }), ""))
        self.assertEqual(Follow.objects.count(), 0)
