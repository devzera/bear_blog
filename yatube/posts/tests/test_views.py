import shutil
import tempfile
import time

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user_dev = User.objects.create_user(username='dev')
        cls.user_arm = User.objects.create_user(username='arm')
        cls.user_mike = User.objects.create_user(username='mike')

        cls.follow = Follow.objects.create(
            user=cls.user_arm,
            author=cls.user_dev
        )

        cls.group_sport = Group.objects.create(
            title='Sports',
            slug='sport',
            description='test test'
        )
        cls.group_game = Group.objects.create(
            title='Games',
            slug='game',
            description='test test'
        )
        for i in range(15):
            Post.objects.create(
                text=f'Text {i}',
                group=cls.group_sport,
                author=cls.user_dev
            )

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            text='Text 15',
            group=cls.group_sport,
            author=cls.user_dev,
            image=cls.uploaded
        )

        cls.last_post = Post.objects.create(
            text='Text 16',
            group=cls.group_sport,
            author=cls.user_dev
        )

        cls.comment = Comment.objects.create(
            text='Some text',
            post=cls.post,
            author=cls.user_dev
        )

        cls.posts_list = Post.objects.select_related(
            'author',
            'group'
        )

        cls.url = {
            'post_create': reverse('posts:post_create'),
            'group_list': reverse(
                'posts:group_list',
                kwargs={'slug': ViewTestCase.group_sport.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': ViewTestCase.user_dev.username}
            ),
            'post_detail': reverse(
                'posts:post_detail',
                kwargs={'post_id': ViewTestCase.post.pk}
            ),
            'post_edit': reverse(
                'posts:post_edit',
                kwargs={'post_id': ViewTestCase.post.pk}
            )
        }
        cls.templates_names = {
            'post_create': 'posts/create_post.html',
            'group_list': 'posts/group_list.html',
            'profile': 'posts/profile.html',
            'post_detail': 'posts/post_detail.html',
            'post_edit': 'posts/create_post.html'
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(ViewTestCase.user_dev)

        self.follower = Client()
        self.follower.force_login(ViewTestCase.user_arm)

        self.not_follower = Client()
        self.not_follower.force_login(ViewTestCase.user_mike)

    def test_correct_templates(self):
        template_names = zip(
            ViewTestCase.url.values(),
            ViewTestCase.templates_names.values()
        )
        for reverse_name, template in template_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse_name
                )
                self.assertTemplateUsed(response, template)

    def test_correct_context(self):
        context_names = {
            ViewTestCase.url['group_list']: ViewTestCase.posts_list.filter(
                group__slug=ViewTestCase.group_sport.slug
            ),
            ViewTestCase.url['profile']: ViewTestCase.posts_list.filter(
                author__username=ViewTestCase.user_dev.username
            ),
        }
        for reverse_name, context in context_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse_name
                )

                posts_list_expected = context
                posts_list = response.context['post_list']

                self.assertEqual(posts_list[1].text, 'Text 15')
                self.assertEqual(posts_list[1].author.username, 'dev')
                self.assertEqual(posts_list[1].group.title, 'Sports')
                self.assertEqual(posts_list[1].image, 'posts/small.gif')

                self.assertEqual(
                    list(posts_list),
                    list(posts_list_expected)
                )

    def test_post_detail_correct_context(self):
        response = self.authorized_client.get(
            ViewTestCase.url['post_detail']
        )
        posts_list_expected = ViewTestCase.posts_list.get(
            pk=ViewTestCase.post.pk
        )
        post = response.context['post']

        self.assertEqual(post.text, 'Text 15')
        self.assertEqual(post.image, 'posts/small.gif')

        self.assertEqual(
            post,
            posts_list_expected
        )

    def test_post_create_correct_form_context(self):
        response = self.authorized_client.get(
            ViewTestCase.url['post_create']
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_form_context(self):
        response = self.authorized_client.get(
            ViewTestCase.url['post_edit']
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_not_in_another_group(self):
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': ViewTestCase.group_game.slug}
            )
        )
        post_expected = ViewTestCase.posts_list.get(
            pk=ViewTestCase.post.pk
        )
        posts_list = response.context['post_list']
        self.assertNotIn(post_expected, posts_list)

    def test_index_first_page_contains_ten_records(self):
        page_names = [
            ViewTestCase.url['group_list'],
            ViewTestCase.url['profile']
        ]
        for reverse_name in page_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse_name
                )
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_index_second_page_contains_five_records(self):
        page_names = [
            ViewTestCase.url['group_list'] + '?page=2',
            ViewTestCase.url['profile'] + '?page=2'
        ]
        for reverse_name in page_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse_name
                )
                self.assertEqual(len(response.context['page_obj']), 7)

    def test_display_comment_post(self):
        response = self.authorized_client.get(
            ViewTestCase.url['post_detail']
        )
        comment = response.context['comments']
        self.assertEqual(comment[0].text, 'Some text')

    def test_display_posts(self):
        new_post = Post.objects.create(
            text='for followers',
            author=ViewTestCase.user_dev
        )

        follower_response = self.follower.get(
            reverse('posts:follow_index')
        )
        post_for_follower = follower_response.context['posts']
        self.assertIn(new_post, post_for_follower)

        not_follower_response = self.not_follower.get(
            reverse('posts:follow_index')
        )
        post_for_not_follower = not_follower_response.context['posts']
        self.assertNotIn(new_post, post_for_not_follower)

    def test_auth_user_can_follow_and_unfollow_on_author(self):
        author = ViewTestCase.user_dev
        user = User.objects.get(username=ViewTestCase.user_mike)
        author_list = user.follower.all()

        self.assertNotIn(author, author_list)

        self.not_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': ViewTestCase.user_dev.username}
            )
        )
        author_list = user.follower.all()
        author_list = [author.author for author in author_list]

        self.assertIn(author, author_list)

        self.not_follower.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': ViewTestCase.user_dev.username}
            )
        )
        author_list = user.follower.all()
        author_list = [author.author for author in author_list]

        self.assertNotIn(author, author_list)

    def test_index_cache(self):
        response = self.client.get(reverse('posts:index'))
        last_post = response.context['page_obj'][0]
        ViewTestCase.last_post.delete()
        last_post_after_del = response.context['page_obj'][0]
        self.assertEqual(last_post, last_post_after_del)

        time.sleep(20)

        response = self.client.get(reverse('posts:index'))
        last_post_after_time = response.context['page_obj'][0]
        self.assertNotEqual(last_post, last_post_after_time)
