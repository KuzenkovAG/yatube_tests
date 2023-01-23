from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Group, Post

User = get_user_model()


def get_posts_count():
    return Post.objects.count()


class TestForms(TestCase):
    """Checking form PostForm for create and edit posts"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.form = PostForm()
        cls.group = Group.objects.create(
            title='Test group',
            slug='test_group',
            description='Group for test',
        )
        cls.another_group = Group.objects.create(
            title='Another group',
            slug='another_group',
            description='Group for changing during edit post',
        )
        cls.post = Post.objects.create(
            group=cls.group,
            text='Post to edit',
            author=cls.user
        )

    def test_creating_post(self):
        """Checking creating new post."""
        initial_post_count = get_posts_count()
        form_content = {
            'group': self.group.pk,
            'text': 'It is test post',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_content,
            folow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            args=[self.user.username]
        ))
        self.assertEqual(get_posts_count(), initial_post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_content.get('text'),
                group=form_content.get('group'),
            ).exists()
        )

    def test_post_edit(self):
        """Checking edition existing post."""
        initial_post_count = get_posts_count()
        form_content = {
            'text': 'Post was edited',
            'group': self.another_group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[self.post.id]),
            data=form_content,
            folow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args=[self.post.id]
        ))
        self.assertEqual(get_posts_count(), initial_post_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_content.get('text'),
                group=form_content.get('group'),
            ).exists()
        )
