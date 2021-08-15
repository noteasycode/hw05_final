from django.contrib.auth import get_user_model
from urllib.parse import quote
from django.test import Client, TestCase
from django.urls import reverse

from .. models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="first-group",
            description="Test_description",
            slug="first",
        )
        cls.test_post = Post.objects.create(
            text="Тестовый текст",
            author=User.objects.create_user(username="den"),
            group=cls.group,
        )

    def setUp(self):
        self.user = PostCreateFormTests.test_post.author
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()

        form_data = {
            "text": "New post",
            "author": self.user.username,
            "group": PostCreateFormTests.group.id
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse("new_post"),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse("index"))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(response.context["page"][0].text, form_data["text"])
        self.assertEqual(
            response.context["page"][0].author.username,
            form_data["author"]
        )
        self.assertEqual(
            response.context["page"][0].group.id,
            form_data["group"]
        )

    def test_create_post_unauthorized_client(self):
        form_data = {
            "text": "Unauthorized post",
            "author": self.user,
            "group": PostCreateFormTests.group.id,
        }
        # Отправляем POST-запрос
        response = self.guest_client.post(
            reverse("new_post"),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse("login") + "?next=" + quote(reverse("new_post"), "")
        )
        self.assertNotEqual(
            self.guest_client.get("/").context["page"][0].text,
            form_data["text"]
        )

    def test_edit_post(self):
        form_data = {
            "text": "changed-post",
            "author": self.user,
            "group": PostCreateFormTests.group.id,
        }
        response = self.authorized_client.post(
            reverse(
                "edit", kwargs={
                "username": self.user,
                "post_id": PostCreateFormTests.test_post.pk,
                }
            ), data=form_data, follow=True
        )
        first_object = response.context["post_of_author"]
        post_text = first_object.text
        self.assertEqual(post_text, form_data["text"])
