from io import StringIO
from unittest import mock

from django.test import TestCase
from django.urls import resolve, reverse
from django.contrib.auth import get_user_model

from ... import views
from ...models import Schema


class TestSchemaDataSetsView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(  # type: ignore
            username="testuser", password="12345"
        )
        cls.schema = Schema.objects.create(
            user=cls.user,
            **{
                "name": "Test schema 1",
                "column_separator": ",",
                "quotechar": '"',
                "fields": [
                    {
                        "name": "Name",
                        "order": 1,
                        "f_type": "name",
                        "f_params": {},
                    }
                ],
            },
        )
        
        cls.schema_2 = Schema.objects.create(
            user=cls.user,
            **{
                "name": "Another schema",
                "column_separator": ",",
                "quotechar": '"',
                "fields": [
                    {
                        "name": "Email",
                        "order": 1,
                        "f_type": "email",
                        "f_params": {},
                    }
                ],
            },
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
        
        self.schema.generated_data.create(num_rows=10)
        self.schema.generated_data.create(num_rows=15)
        generated = self.schema.generated_data.create(num_rows=20)
        generated.file.save("test.csv", StringIO("dummy data"))
        
        # add generated data to see if it listed on a wrong page
        self.schema_2.generated_data.create(num_rows=1337)
        
        response = self.client.get(self.VIEW_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["schema"].generated_data.count(), 3)
        self.assertContains(response, "Processing", count=2)
        self.assertContains(response, "Ready", count=1)
        self.assertContains(response, generated.file.url)
        
    def test_lists_only_own_datasets(self):
        self.schema.generated_data.create(num_rows=10)      
        
        user_2 = get_user_model().objects.create_user(  # type: ignore
            username="testuser_2", password="12345"
        )
        self.client.force_login(user_2)
        
        response = self.client.get(reverse("schema:datasets", kwargs={"pk": self.schema.pk}))
        self.assertEqual(response.status_code, 404)
        
    def test_request_generation(self):
        self.client.force_login(self.user)
        with mock.patch.object(Schema, 'run_generate_task') as mock_generate:
            response = self.client.post(self.VIEW_URL, {"num_rows": 10})
            mock_generate.assert_called_once_with(10)
