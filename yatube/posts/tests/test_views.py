from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Group, Post

User = get_user_model()


class TestViews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Группа для теста',
            slug='for_test',
            description='Описание тестовой группы'
        )
        cls.user = User.objects.create_user(username='test_user')
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user,
            text='Текст поста',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_used_templates(self):
        templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                args=[self.group.slug]
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                args=[self.user.username]
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                args=[self.post.id]
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                args=[self.post.id]
            ): 'posts/create_post.html',
        }
        for address, template in templates.items():
            with self.subTest(view=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_context_title(self):
        titles = {
            reverse('posts:post_create'): 'Новый пост',
            reverse(
                'posts:post_edit',
                args=[self.post.id]
            ): 'Редактировать пост',
        }
        for address, title in titles.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.context.get('title'), title)

    def test_context_list_of_posts(self):
        """Check post lists"""
        url = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[self.group.slug]),
            reverse('posts:profile', args=[self.user.username]),
        ]
        for url in url:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                first_object = response.context.get('page_obj')[0]
                self.assertEqual(first_object.author, self.user)
                self.assertEqual(first_object.group, self.group)
                self.assertEqual(first_object.text, self.post.text)

    def test_post_detail_page_correct_context(self):
        """Context on page of post detail."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=[self.post.id])
        )
        post_object = response.context.get('post')
        self.assertEqual(post_object.id, self.post.id)

    def test_post_create_and_edit_pages_form(self):
        """Context on page of creating post and editing post."""
        urls = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', args=[self.post.id])
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                form = response.context.get('form')
                self.assertIsInstance(form, PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get('form').fields.get(
                            value
                        )
                        self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Группа для теста',
            slug='for_test',
            description='Описание тестовой группы'
        )
        cls.user = User.objects.create_user(username='test_user')
        for i in range(1, 14):
            Post.objects.create(
                group=cls.group,
                author=cls.user,
                text=f'Текст {i}-го поста'
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator(self):
        """Inspection of quantity of post on 1st and 2nd page of paginator."""
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[self.group.slug]),
            reverse('posts:profile', args=[self.user.username]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.max_post_on_page = 10
                self.check_objects_on_first_page(url)
                self.check_objects_on_second_page(url)

    def check_objects_on_first_page(self, url):
        """Inspection of quantity of post on 1st page of paginator."""
        self.assertEqual(self.quantity_of_posts(url), self.max_post_on_page)

    def check_objects_on_second_page(self, url):
        """Inspection of quantity of post on 2nd page of paginator."""
        url = url + '?page=2'
        post_quantity = 3
        self.assertEqual(self.quantity_of_posts(url), post_quantity)

    def quantity_of_posts(self, url):
        """Quantity of posts on page received by url."""
        response = self.authorized_client.get(url)
        return len(response.context.get('page_obj'))


class TestCreatingPost(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Группа для теста',
            slug='group',
            description='Описание тестовой группы'
        )
        cls.group_another = Group.objects.create(
            title='Группа для теста',
            slug='group_another',
            description='Другая тестовой группы'
        )

        cls.user = User.objects.create_user(username='test_user')
        cls.user_another = User.objects.create_user(username='User_another')
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user,
            text='Текст поста',
        )
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user_another,
            text='Текст созданного другим пользователем',
        )
        cls.post = Post.objects.create(
            group=cls.group_another,
            author=cls.user_another,
            text='Текст созданного другим пользователем в другой группе',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_page_group_correct_posts(self):
        """Page of group show only own group posts."""
        response = self.authorized_client.get(
            reverse('posts:group_list', args=[self.group.slug]))
        posts = response.context.get('page_obj')
        for post in posts:
            self.assertEqual(post.group, self.group)

    def test_page_profile_correct_posts(self):
        """Page of profile show only own user posts."""
        response = self.authorized_client.get(
            reverse('posts:profile', args=[self.user.username])
        )
        posts = response.context.get('page_obj')
        for post in posts:
            self.assertEqual(post.author, self.user)

    def test_post_not_in_other_group(self):
        """Post with other group not show on group page."""
        response = self.authorized_client.get(
            reverse('posts:group_list', args=[self.group_another.slug])
        )
        posts = response.context.get('page_obj')
        for post in posts:
            self.assertNotEqual(post.group, self.group)
