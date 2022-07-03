from django.test import TestCase
from django.urls import resolve, reverse
from django.contrib.auth import get_user_model

from ... import views
from ...models import NameColumn, RandomIntColumn, Schema


class TestSchemaListView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="testuser", password="12345"
        )
        schema = Schema.objects.create(name="Test schema", user=cls.user)
        NameColumn.objects.create(name="Full name", order=1, schema=schema)

        schema_2 = Schema.objects.create(name="Test schema 2", user=cls.user)
        RandomIntColumn.objects.create(
            name="Age", min=15, max=80, order=2, schema=schema_2
        )

        cls.user_2 = get_user_model().objects.create_user(
            username="testuser_2", password="12345"
        )
        schema_3 = Schema.objects.create(name="Test schema 2", user=cls.user_2)
        RandomIntColumn.objects.create(
            name="Height", min=140, max=225, order=2, schema=schema_3
        )

    VIEW_URL = reverse("schema:list")

    def test_url_resolves_to_view(self):
        self.assertIs(
            resolve(self.VIEW_URL).func.view_class, views.ListSchemasView
        )

    def test_call_view_deny_anonymous(self):
        response = self.client.get(self.VIEW_URL, follow=True)
        self.assertRedirects(
            response, reverse("users:login") + "?next=" + self.VIEW_URL
        )

        response = self.client.post(self.VIEW_URL, follow=True)
        self.assertRedirects(
            response, reverse("users:login") + "?next=" + self.VIEW_URL
        )

    def test_call_view_allows_registered(self):
        self.client.force_login(self.user)
        response = self.client.get(self.VIEW_URL)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        self.client.force_login(self.user)
        response = self.client.get(self.VIEW_URL)
        self.assertTemplateUsed(response, "schema/list.html")

    def test_list_own_schemas(self):
        self.client.force_login(self.user)
        response = self.client.get(self.VIEW_URL)
        user_schemas = Schema.objects.filter(user=self.user)
        self.assertQuerysetEqual(
            response.context["schemas"], user_schemas, ordered=False
        )
        self.assertEqual(user_schemas.count(), 2)

        self.client.force_login(self.user_2)
        response = self.client.get(self.VIEW_URL)
        user_schemas = Schema.objects.filter(user=self.user_2)
        self.assertQuerysetEqual(
            response.context["schemas"], user_schemas, ordered=False
        )
        self.assertEqual(user_schemas.count(), 1)

    def test_template_renders_schemas_and_links_to_datasets(self):
        self.client.force_login(self.user)
        response = self.client.get(self.VIEW_URL)
        for schema in Schema.objects.filter(user=self.user):
            url = reverse("schema:datasets", kwargs={"pk": schema.pk})
            schema_anchor = f"<a href='{url}' class='text-decoration-none'>{schema.name}</a>"

            self.assertContains(response, schema_anchor, html=True)
