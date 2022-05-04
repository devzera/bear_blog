from django.test import TestCase
from posts.models import Group, Post, User


class ModelTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Давно выяснено, что при оценке дизайна и дуб',
            author=cls.user
        )

    def test_verbose_name(self):
        post = ModelTestCase.post
        field_verboses = {
            'text': 'Описание',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                verbose_name = post._meta.get_field(field).verbose_name
                self.assertEqual(
                    verbose_name,
                    expected_value
                )

    def test_help_text(self):
        post = ModelTestCase.post
        help_text = post._meta.get_field('text').help_text
        self.assertEqual(help_text, 'описание')

    def test_post_has_correct_object_name(self):
        post = ModelTestCase.post
        expected_value = post.text[:15]
        self.assertEqual(str(post), expected_value)

    def test_group_has_correct_object_name(self):
        group = ModelTestCase.group
        expected_value = group.title
        self.assertEqual(str(group), expected_value)
