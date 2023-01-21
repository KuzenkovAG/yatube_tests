from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Post

User = get_user_model()


def get_posts_count():
    return Post.objects.all().count()


class TestForms(TestCase):
    """Checking form PostForm for create and edit posts"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.form = PostForm()
        cls.post = Post.objects.create(
            text='Post to edit',
            author=cls.user
        )

    def test_creating_post(self):
        """Checking creating new post."""
        post_count = get_posts_count()
        form_content = {
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
        self.assertEqual(get_posts_count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_content.get('text'),
            ).exists()
        )

    def test_post_edit(self):
        """Checking edition existing post."""
        post_count = Post.objects.all().count()
        form_content = {
            'text': 'Post was edited',
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
        self.assertEqual(Post.objects.all().count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_content.get('text'),
            ).exists()
        )
