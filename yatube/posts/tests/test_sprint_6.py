import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from urllib.parse import quote

from .. models import Comment, Follow, Group, Post
from .. forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mktemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestsForSixthSprint(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="first-group",
            description="Test_description",
            slug="first",
        )
        cls.test_post = Post.objects.create(
            text="Text for post",
            author=User.objects.create_user(username="test_user"),
            group=TestsForSixthSprint.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = TestsForSixthSprint.test_post.author
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.following_user = User.objects.create_user(username="new_user")
        self.following_client = Client()
        self.following_client.force_login(self.following_user)
        self.introvert = User.objects.create_user(username="introvert")
        self.introvert_client = Client()
        self.introvert_client.force_login(self.introvert)

    def test_create_post_with_image(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name="small.jpeg",
            content=small_image,
            content_type="image/jpeg"
        )
        form_data = {
            "group": TestsForSixthSprint.group.pk,
            "text": "Second post",
            "image": uploaded,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse("new_post"),
            data=form_data,
            follow=True
        )
        second_post = Post.objects.get(
            text=form_data["text"],
            image="posts/small.jpeg"
        )
        pages_list = [
            reverse("index"),
            reverse("group", kwargs={
                "slug": TestsForSixthSprint.group.slug
            }),
            reverse("profile", kwargs={
                "username": second_post.author
            }),
            reverse("post", kwargs={
                "username": second_post.author,
                "post_id": second_post.pk
            }
                    )
        ]

        self.assertRedirects(response, reverse("index"))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, передалась ли картинка в контекст
        for url in pages_list:
            with self.subTest(reverse_name=url):
                test_response = self.authorized_client.get(url)
                if url == f"/{second_post.author}/{second_post.pk}/":
                    self.assertTrue(
                        test_response.context["post_of_author"].image
                    )
                else:
                    self.assertTrue(
                        test_response.context["page"][0].image
                    )

    def test_404(self):
        response = self.authorized_client.get("leo/")
        self.assertTemplateUsed(response, "misc/404.html")

    def test_index_page_contains_cache(self):
        post = Post.objects.create(text="Cached post", author=self.user)
        cache.clear()
        response = self.authorized_client.get(reverse("index"))
        content = response.content
        post.delete()
        response = self.authorized_client.get(reverse("index"))
        self.assertEqual(response.content, content)
        cache.clear()
        response = self.authorized_client.get(reverse("index"))
        self.assertNotEqual(response.content, content)

    def test_following(self):
        post = Post.objects.create(
            text="Post for followers",
            author=self.following_user)
        Follow.objects.create(user=self.user, author=self.following_user)
        response = self.authorized_client.get(
            reverse("follow_index")
        )
        without_follow_resp = self.introvert_client.get(
            reverse("follow_index")
        )
        self.assertEqual(response.context["page"][0].text, post.text)
        self.assertNotEqual(without_follow_resp.context, response.context)
        self.assertEqual(Follow.objects.count(), 1)
        self.authorized_client.get(
            reverse("profile_unfollow", kwargs={"username": post.author})
        )
        self.assertEqual(Follow.objects.count(), 0)

    def test_comments(self):
        form_data = {
            "post": TestsForSixthSprint.test_post.pk,
            "author": TestsForSixthSprint.test_post.author,
            "text": "Second comment",

        }
        response = self.authorized_client.post(
            reverse("add_comment", kwargs={
                "username": self.user,
                "post_id": TestsForSixthSprint.test_post.pk
            }),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse("post", kwargs={
            "username": self.user,
            "post_id": TestsForSixthSprint.test_post.pk
        }))
        self.assertEqual(Comment.objects.count(), 1)
        response = self.guest_client.post(
            reverse("add_comment", kwargs={
                "username": self.user,
                "post_id": TestsForSixthSprint.test_post.pk
            }),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse(
            "login"
        ) + "?next=" + quote(reverse(
            "add_comment", kwargs={
                "username": self.user,
                "post_id": TestsForSixthSprint.test_post.pk
            }), ""))
        self.assertEqual(Comment.objects.count(), 1)
