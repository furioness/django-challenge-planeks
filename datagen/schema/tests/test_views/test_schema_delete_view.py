from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve, reverse

from ... import views
from ...models import NameColumn, Schema


class TestDeleteSchemaView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="testuser", password="12345"
        )
        cls.schema = Schema.objects.create(name="Test schema", user=cls.user)
        NameColumn.objects.create(name="Full name", order=1, schema=cls.schema)

    @property
    def VIEW_URL(self):
        return reverse("schema:delete", kwargs={"pk": self.schema.pk})

    def test_url_resolves_to_view(self):
        self.assertIs(
            resolve(self.VIEW_URL).func.view_class, views.DeleteSchemaView
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
        self.assertTemplateUsed(response, "schema/delete.html")

    def test_schema_deleted(self):
        self.client.force_login(self.user)
        response = self.client.post(self.VIEW_URL)
        self.assertRedirects(response, reverse("schema:list"))
        with self.assertRaises(self.schema.DoesNotExist):
            self.schema.refresh_from_db()

    def test_only_owner_can_delete(self):
        user_2 = get_user_model().objects.create_user(
            username="testuser_2", password="12345"
        )
        self.client.force_login(user_2)
        response = self.client.post(self.VIEW_URL)
        self.assertEqual(response.status_code, 404)

    def test_returns_404_for_non_existent(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("schema:delete", kwargs={"pk": self.schema.pk + 1})
        )
        self.assertEqual(response.status_code, 404)
