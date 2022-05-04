from django.test import TestCase


class TestTemplate(TestCase):

    def test_404_use_correct_template(self):
        response = self.client.get('/error/')
        self.assertTemplateUsed(response, 'core/404.html')
