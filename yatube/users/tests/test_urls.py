from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class URLTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='dev')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_urls_status_code(self):
        url_names_get_200 = [
            '/auth/signup/',
            '/auth/logout/',
            '/auth/login/',
            '/auth/password_reset/',
            '/auth/password_reset/done/',
            '/auth/reset/done/'
        ]
        for url in url_names_get_200:
            with self.subTest(url=url):
                response = URLTestCase.authorized_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK.value
                )

        url_names_get_302 = [
            '/auth/password_change/',
            '/auth/password_change/done/',
        ]
        for url in url_names_get_302:
            with self.subTest(url=url):
                response = URLTestCase.authorized_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.FOUND.value
                )
