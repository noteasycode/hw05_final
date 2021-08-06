from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from .. models import Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД
        cls.test_group = Group.objects.create(
            title="Test-title",
            description="Test_description",
            slug="test-slug",
        )
        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=User.objects.create_user(username="test_author"),
            group=cls.test_group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = PostPagesTests.post.author
        self.not_author = User.objects.create_user(username="not_author")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)

    # Проверяем используемые шаблоны
    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: name"
        templates_pages_names = {
            "index.html": reverse("index"),
            "group.html": (
                reverse("group", kwargs={
                    "slug": PostPagesTests.test_group.slug
                })
            ),
            "new.html": reverse("new_post"),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("index"))
        first_object = response.context["page"][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        self.assertEqual(post_text_0, PostPagesTests.post.text)
        self.assertEqual(post_author_0, PostPagesTests.post.author)

    def test_group_page_shows_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            "group", kwargs={"slug": PostPagesTests.test_group.slug})
        )
        first_object = response.context["page"][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        self.assertEqual(post_text_0, PostPagesTests.post.text)
        self.assertEqual(post_author_0, PostPagesTests.post.author)

    def test_new_post_page_shows_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("profile", kwargs={
            "username": PostPagesTests.post.author}))
        first_object = response.context["page"][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        self.assertEqual(post_text_0, PostPagesTests.post.text)
        self.assertEqual(post_author_0, PostPagesTests.post.author)

    def test_post_edit_page_shows_correct_context(self):
        """Шаблон страницы редактирования поста сформирован
        с правильным контекстом."""
        response = self.authorized_client.get(reverse("edit", kwargs={
            "username": PostPagesTests.post.author,
            "post_id": PostPagesTests.post.pk,
        }))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_post_page_shows_correct_context(self):
        """Шаблон страницы отдельного поста сформирован с
         правильным контекстом."""
        response = self.authorized_client.get(reverse("post", kwargs={
            "username": PostPagesTests.post.author,
            "post_id": PostPagesTests.post.pk,
        }))
        first_object = response.context["post_of_author"]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        self.assertEqual(post_text_0, PostPagesTests.post.text)
        self.assertEqual(post_author_0, PostPagesTests.post.author)

    def test_post_exists_at_another_group(self):
        """Пост не попадает в группу, для которой не был предназначен."""
        wrong_group = Group.objects.create(
            title="wrong-title",
            description="Don`t use this group"
                        "for post creation",
            slug="wrong-group",
        )
        response = self.authorized_client.get(reverse("group", kwargs={
            "slug": wrong_group.slug,
        }))
        self.assertFalse(response.context["page"])


class PaginatorViewsTest(TestCase):
    def setUp(self):
        # Создаем авторизованный клиент
        self.user = User.objects.create_user(username="denis")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.test_group = Group.objects.create(
            title="Test-title",
            description="Test_description",
            slug="test-slug",
        )
        for i in range(13):
            Post.objects.create(
                text=f"Тестовый текст_{i}",
                author=self.user,
                group=self.test_group
            ).save()
        self.objects = Post.objects
        self.data = [
            {"text": obj.text, "author": obj.author, "group": obj.group}
            for obj in self.objects.all()
        ]

    def test_page_contains_ten_records(self):
        pages_list = [
            reverse("index"),
            reverse("group", kwargs={"slug": self.test_group.slug}),
            reverse("profile", kwargs={"username": self.user}),
        ]
        for url in pages_list:
            with self.subTest(reverse_name=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    len(response.context.get("page").object_list), 10
                )
