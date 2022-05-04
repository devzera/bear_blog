from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User


class URLTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='dev')

        cls.post = Post.objects.create(
            text='Text 1',
            author=cls.user
        )
        cls.group = Group.objects.create(
            title='test group 1',
            slug='group',
            description='content test group 1'
        )

        cls.url = [
            reverse(
                'posts:group_list',
                kwargs={'slug': URLTestCase.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': URLTestCase.user.username}
            ),
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': URLTestCase.post.pk}
            )
        ]
        cls.templates_names = [
            'posts/group_list.html',
            'posts/profile.html',
            'posts/create_post.html',
            'posts/create_post.html'
        ]

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(URLTestCase.user)

    def test_url_for_anonymous(self):
        url_names = {
            '/create/': '/auth/login/?next=/create/',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': URLTestCase.post.pk}
            ): '/auth/login/?next=%2Fposts%2F1%2Fedit%2F',
            reverse(
                'posts:add_comment',
                kwargs={'post_id': URLTestCase.post.pk}
            ): '/auth/login/?next=/posts/1/comment/'
        }
        for url, redirect_url in url_names.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_urls_status_code(self):
        url_names_get_200 = URLTestCase.url
        for url in url_names_get_200:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK.value
                )

    def test_urls_uses_correct_template(self):
        templates_url_names = zip(URLTestCase.url, URLTestCase.templates_names)
        for url, template in templates_url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
