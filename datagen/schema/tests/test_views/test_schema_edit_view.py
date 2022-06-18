from django.test import TestCase
from django.urls import resolve, reverse
from django.contrib.auth import get_user_model

from ... import views
from ...models import BaseColumn, NameColumn, RandomIntColumn, Schema


class TestEditSchemaView(TestCase):
    """Test just edit specific problems.
    Other edge cases like data validation and error renering
    are covered by schema_create and form tests."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(  # type: ignore
            username="testuser", password="12345"
        )
        cls.schema = Schema.objects.create(
            name="Test schema",
            column_separator=",",
            quotechar='"',
            user=cls.user,
        )
        NameColumn.objects.create(name="Name", order=1, schema=cls.schema)
        RandomIntColumn.objects.create(
            name="Age", order=2, max=55, min=5, schema=cls.schema
        )

    @property
    def VIEW_URL(self):
        return reverse("schema:edit", kwargs={"pk": self.schema.pk})

    def test_url_resolves_to_view(self):
        self.assertIs(
            resolve(self.VIEW_URL).func.view_class, views.EditSchemaView
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
        self.assertTemplateUsed(response, "schema/edit.html")  # type: ignore

    def test_shows_correct_schema(self):
        self.client.force_login(self.user)
        response = self.client.get(self.VIEW_URL)
        self.assertEqual(response.context["schema"], self.schema)  # type: ignore

    def test_shows_only_to_owner(self):
        user_2 = get_user_model().objects.create_user(  # type: ignore
            username="testuser_2", password="12345"
        )
        self.client.force_login(user_2)
        response = self.client.get(self.VIEW_URL)
        self.assertEqual(response.status_code, 404)

    def test_returns_404_if_schema_does_not_exist(self):
        url = reverse("schema:edit", kwargs={"pk": self.schema.pk + 1})
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_template_indicates_editing(self):
        self.client.force_login(self.user)
        response = self.client.get(self.VIEW_URL)
        self.assertContains(response, f"<title>Edit {self.schema.name}</title>", html=True)  # type: ignore
        self.assertContains(response, f'<h2 class="d-inline-block">Edit {self.schema.name}</h2>', html=True)  # type: ignore
