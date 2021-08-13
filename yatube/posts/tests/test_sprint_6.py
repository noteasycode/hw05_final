import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from .. models import Group, Post
from .. forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mktemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostWithImageTests(TestCase):
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
            group=PostWithImageTests.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = PostWithImageTests.test_post.author
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

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
            "group": PostWithImageTests.group.pk,
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
                "slug": PostWithImageTests.group.slug
            }),
            reverse("profile", kwargs={
                "username": second_post.author
            }),
            reverse("post", kwargs={
                "username": second_post.author,
                "post_id": second_post.pk
                    })
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
