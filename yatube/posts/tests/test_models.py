# from django.test import TestCase
#
# from .. models import Group, Post, User
#
#
# class PostModelTest(TestCase):
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.post = Post.objects.create(
#             text="Тестовый текст",
#             author=User.objects.create_user(username="TestUser")
#         )
#
#     def test_object_name_is_text_field(self):
#         post = PostModelTest.post
#         expected_object_name = post.text
#         self.assertEqual(expected_object_name, str(post))
#
#
# class GroupModelTest(TestCase):
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.group = Group.objects.create(
#             title="Тестовый заголовок",
#             description="Тестовое описание"
#         )
#
#     def test_object_name_is_title_field(self):
#         group = GroupModelTest.group
#         expected_object_name = group.title
#         self.assertEqual(expected_object_name, str(group))
