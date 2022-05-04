import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormsTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='dev')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Group 1',
            slug='group1',
            description='Test test'
        )
        cls.post = Post.objects.create(
            text='Давно выяснено, что при оценке дизайна и дуб',
            author=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Some text 2',
            'group': FormsTestCase.group.pk,
            'post_id': '1',
            'image': uploaded
        }
        response = FormsTestCase.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'dev'})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        form_data = {
            'text': 'new Some text 2',
            'group': FormsTestCase.group.pk,
            'post_id': '1'
        }
        response = FormsTestCase.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': form_data['post_id']}
            ),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text='new Some text 2',
                group=FormsTestCase.group.pk
            ).exists()
        )

        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
