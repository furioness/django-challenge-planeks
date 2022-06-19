from io import StringIO
from unittest import mock

from django.test import TestCase
from django.urls import resolve, reverse
from django.contrib.auth import get_user_model

from ... import views
from ...models import NameColumn, RandomIntColumn, Schema


class TestSchemaDataSetsView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(  # type: ignore
            username="testuser", password="12345"
        )
        cls.schema = Schema.objects.create(name="Test schema", user=cls.user)
        NameColumn.objects.create(name="Full name", order=1, schema=cls.schema)

        cls.schema_2 = Schema.objects.create(
            name="Test schema 2", user=cls.user
        )
        RandomIntColumn.objects.create(
            name="Age", min=15, max=80, order=2, schema=cls.schema_2
        )

    @property
    def VIEW_URL(self):
        return reverse("schema:datasets", kwargs={"pk": self.schema.pk})

    def test_url_resolves_to_view(self):
        self.assertIs(
            resolve(self.VIEW_URL).func.view_class, views.SchemaDataSetsView
        )

    def test_call_view_deny_anonymous(self):
        response = self.client.get(self.VIEW_URL, follow=True)
        self.assertRedirects(response, reverse("users:login") + "?next=" + self.VIEW_URL)  # type: ignore

        response = self.client.post(self.VIEW_URL, follow=True)
        self.assertRedirects(response, reverse("users:login") + "?next=" + self.VIEW_URL)  # type: ignore

    def test_call_view_allows_registered(self):
        self.client.force_login(self.user)
        response = self.client.get(self.VIEW_URL)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        self.client.force_login(self.user)
        response = self.client.get(self.VIEW_URL)
        self.assertTemplateUsed(response, "data/list.html")  # type: ignore

    def test_render_datasets_list(self):
        self.client.force_login(self.user)

        self.schema.datasets.create(num_rows=10)
        self.schema.datasets.create(num_rows=15)
        generated = self.schema.datasets.create(num_rows=20)
        generated.file.save("test.csv", StringIO("dummy data"))

        # add generated data to see if it listed on a wrong page
        self.schema_2.datasets.create(num_rows=1337)

        response = self.client.get(self.VIEW_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["schema"].datasets.count(), 3)  # type: ignore
        self.assertContains(response, "Processing", count=2)
        self.assertContains(response, "Ready", count=1)
        self.assertContains(response, generated.file.url)

    def test_lists_only_own_datasets(self):
        self.schema.datasets.create(num_rows=10)

        user_2 = get_user_model().objects.create_user(  # type: ignore
            username="testuser_2", password="12345"
        )
        self.client.force_login(user_2)

        response = self.client.get(
            reverse("schema:datasets", kwargs={"pk": self.schema.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_request_generation(self):
        self.client.force_login(self.user)
        with mock.patch.object(Schema, "run_generate_task") as mock_generate:
            self.client.post(self.VIEW_URL, {"num_rows": 10})
            mock_generate.assert_called_once_with(10)
