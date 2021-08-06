from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from .. models import Group, Post

User = get_user_model()


class StaticURLTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get("/")
        self.assertEqual(response.status_code, 200)


class GroupURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_group = Group.objects.create(
            title="Test-title",
            description="Test_description",
            slug="test-slug",
        )
        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=User.objects.create_user(username="test_author"),
            group=GroupURLTests.test_group,
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
            "/": "index.html",
            "/group/test-slug/": "group.html",
            "/new/": "new.html",
            "/test_author/": "profile.html",
            "/test_author/1/": "post.html",
            "/test_author/1/edit/": "new.html",
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
                self.assertEqual(response.status_code, 200)

        for adress in templates_url_names.keys():
            with self.subTest(adress=adress):
                response = self.not_author_client.get(adress)
                if adress == "/test_author/1/edit/":
                    self.assertEqual(response.status_code, 302)
                else:
                    self.assertEqual(response.status_code, 200)

    def test_post_edit_url_redirect_anonymous(self):
        """Страница /<username>/<post_id>/edit/ перенаправляет
        анонимного пользователя."""
        response = self.guest_client.get(
            "/test_author/1/edit/",
            follow=True
        )
        self.assertRedirects(response,
                             "/auth/login/?next=/test_author/1/edit/"
                             )
