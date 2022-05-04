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

        cls.user = User.objects.create_user(username='dev')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.new_user = User.objects.create_user(username='arm')
        cls.follower = Client()
        cls.follower.force_login(cls.new_user)

        cls.new_user_2 = User.objects.create_user(username='mike')
        cls.not_follower = Client()
        cls.not_follower.force_login(cls.new_user_2)

        cls.follow = Follow.objects.create(
            user=cls.new_user,
            author=cls.user
        )

        cls.group_1 = Group.objects.create(
            title='Group 1',
            slug='group1',
            description='test test'
        )
        cls.group_2 = Group.objects.create(
            title='Group 2',
            slug='group2',
            description='test test'
        )
        for i in range(15):
            Post.objects.create(
                text=f'Text {i}',
                group=cls.group_1,
                author=cls.user
            )
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
        cls.post = Post.objects.create(
            text='Text 15',
            group=cls.group_1,
            author=cls.user,
            image=uploaded
        )

        cls.comment = Comment.objects.create(
            text='Some text',
            post=cls.post,
            author=cls.user
        )

        cls.posts_list = Post.objects.select_related(
            'author',
            'group'
        )

        cls.url = {
            'post_create': reverse('posts:post_create'),
            'group_list': reverse(
                'posts:group_list',
                kwargs={'slug': 'group1'}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': 'dev'}
            ),
            'post_detail': reverse(
                'posts:post_detail',
                kwargs={'post_id': '16'}
            ),
            'post_edit': reverse(
                'posts:post_edit',
                kwargs={'post_id': '16'}
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

    # Template test
    def test_correct_templates(self):
        template_names = zip(
            ViewTestCase.url.values(),
            ViewTestCase.templates_names.values()
        )
        for reverse_name, template in template_names:
            with self.subTest(reverse_name=reverse_name):
                response = ViewTestCase.authorized_client.get(
                    reverse_name
                )
                self.assertTemplateUsed(response, template)

    # Correct context test
    def test_correct_context(self):
        context_names = {
            ViewTestCase.url['group_list']: ViewTestCase.posts_list.filter(
                group__slug='group1'
            ),
            ViewTestCase.url['profile']: ViewTestCase.posts_list.filter(
                author__username='dev'
            ),
        }
        for reverse_name, context in context_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = ViewTestCase.authorized_client.get(
                    reverse_name
                )

                posts_list_expected = context
                posts_list = response.context['post_list']

                post_title_0 = posts_list[0].text
                post_author_0 = posts_list[0].author.username
                post_group_0 = posts_list[0].group.title
                post_image_0 = posts_list[0].image

                self.assertEqual(post_title_0, 'Text 15')
                self.assertEqual(post_author_0, 'dev')
                self.assertEqual(post_group_0, 'Group 1')
                self.assertEqual(post_image_0, 'posts/small.gif')

                self.assertEqual(
                    list(posts_list),
                    list(posts_list_expected)
                )

    def test_post_detail_correct_context(self):
        response = ViewTestCase.authorized_client.get(
            ViewTestCase.url['post_detail']
        )
        posts_list_expected = ViewTestCase.posts_list.get(
            pk='16'
        )
        post = response.context['post']

        post_title = post.text
        post_image = post.image

        self.assertEqual(post_title, 'Text 15')
        self.assertEqual(post_image, 'posts/small.gif')

        self.assertEqual(
            post,
            posts_list_expected
        )

    def test_post_create_correct_form_context(self):
        response = ViewTestCase.authorized_client.get(
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
        response = ViewTestCase.authorized_client.get(
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

    # Post of group1 not in group2
    def test_post_group_not_in_another_group(self):
        response = ViewTestCase.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'group2'})
        )
        post_expected = ViewTestCase.posts_list.get(
            pk='1'
        )
        posts_list = response.context['post_list']
        self.assertNotIn(post_expected, posts_list)

    # Paginator test
    def test_index_first_page_contains_ten_records(self):
        page_names = [
            ViewTestCase.url['group_list'],
            ViewTestCase.url['profile']
        ]
        for reverse_name in page_names:
            with self.subTest(reverse_name=reverse_name):
                response = ViewTestCase.authorized_client.get(
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
                response = ViewTestCase.authorized_client.get(
                    reverse_name
                )
                self.assertEqual(len(response.context['page_obj']), 6)

    def test_display_comment_post(self):
        response = ViewTestCase.authorized_client.get(
            ViewTestCase.url['post_detail']
        )
        comment = response.context['comments']
        comment_text = comment[0].text
        self.assertEqual(comment_text, 'Some text')

    def test_display_posts(self):
        new_post = Post.objects.create(
            text='for followers',
            author=ViewTestCase.user
        )

        follower_response = ViewTestCase.follower.get(
            reverse('posts:follow_index')
        )
        post_for_follower = follower_response.context['posts']
        self.assertIn(new_post, post_for_follower)

        not_follower_response = ViewTestCase.not_follower.get(
            reverse('posts:follow_index')
        )
        post_for_not_follower = not_follower_response.context['posts']
        self.assertNotIn(new_post, post_for_not_follower)

    def test_auth_user_can_follow_and_unfollow_on_author(self):
        # Not follower

        author = ViewTestCase.user
        user = User.objects.get(username=ViewTestCase.new_user_2)
        author_list = user.follower.all()

        self.assertNotIn(author, author_list)

        # Follow

        ViewTestCase.not_follower.get(
            reverse('posts:profile_follow', kwargs={'username': 'dev'})
        )
        author_list = user.follower.all()
        author_list = [author.author for author in author_list]

        self.assertIn(author, author_list)

        # Unfollow

        ViewTestCase.not_follower.get(
            reverse('posts:profile_unfollow', kwargs={'username': 'dev'})
        )
        author_list = user.follower.all()
        author_list = [author.author for author in author_list]

        self.assertNotIn(author, author_list)

    def test_index_cache(self):
        response = self.client.get(reverse('posts:index'))
        last_post = response.context['page_obj'][0]
        ViewTestCase.post.delete()
        last_post_after_del = response.context['page_obj'][0]
        self.assertEqual(last_post, last_post_after_del)

        time.sleep(20)

        response = self.client.get(reverse('posts:index'))
        last_post_after_time = response.context['page_obj'][0]
        self.assertNotEqual(last_post, last_post_after_time)
