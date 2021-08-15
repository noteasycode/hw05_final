from django.contrib.auth import get_user_model
from django.test import TestCase

from .. models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_1 = Post.objects.create(
            text="Тестовый текст",
            author=User.objects.create_user(username="TestUser")
        )

    def test_object_name_is_text_field(self):
        post = PostModelTest.post_1
        expected_object_name = post.text
        self.assertEqual(expected_object_name, str(post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_1 = Group.objects.create(
            title="Тестовый заголовок",
            description="Тестовое описание",
            slug="group-slug"
        )

    def test_object_name_is_title_field(self):
        group = GroupModelTest.group_1
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
