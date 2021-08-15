from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .. models import Group, Post

User = get_user_model()


class PaginatorViewsTest(TestCase):
    def setUp(self):
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

    def tearDown(self):
        Group.objects.all().delete()
        Post.objects.all().delete()

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
                    len(response.context.get("page").object_list), 10)
