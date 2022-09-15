from django.contrib.auth import get_user_model
from django.urls import resolve, reverse

from rest_framework.test import APITestCase

from ...models import NameColumn, Schema, Dataset
from ...rest_api import views
from ...rest_api.serializers import SchemaSerializer, DatasetSerializer


class TestSchemaViewSet(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="testuser", password="12345"
        )
        cls.schema = Schema.objects.create(
            **{
                "name": "People",
                "column_separator": ";",
                "quotechar": "!",
            },
            user=cls.user
        )
        cls.name_column = NameColumn.objects.create(
            name="Vasya", order=1, schema=cls.schema
        )

        # second set of user/schema to check filtering
        user2 = get_user_model().objects.create_user(
            username="testuser2", password="67890"
        )
        Schema.objects.create(
            **{
                "name": "Creatures",
                "column_separator": ";",
                "quotechar": "!",
            },
            user=user2
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_urls_resolves(self):
        self.assertIs(
            resolve(reverse("schema:schemas-list")).func.cls,
            views.SchemaViewSet,
        )
        self.assertIs(
            resolve(
                reverse("schema:schemas-detail", kwargs={"pk": 1})
            ).func.cls,
            views.SchemaViewSet,
        )

    def test_is_auth_restricted(self):
        self.client.logout()

        response = self.client.get(reverse("schema:schemas-list"))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(reverse("schema:schemas-list"))
        self.assertEqual(response.status_code, 403)

        response = self.client.patch(reverse("schema:schemas-list"))
        self.assertEqual(response.status_code, 403)

        response = self.client.put(reverse("schema:schemas-list"))
        self.assertEqual(response.status_code, 403)

        response = self.client.get(
            reverse("schema:schemas-detail", kwargs={"pk": 1})
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.post(
            reverse("schema:schemas-detail", kwargs={"pk": 1})
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.patch(
            reverse("schema:schemas-detail", kwargs={"pk": 1})
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.put(
            reverse("schema:schemas-detail", kwargs={"pk": 1})
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.delete(
            reverse("schema:schemas-detail", kwargs={"pk": 1})
        )
        self.assertEqual(response.status_code, 403)

    def test_list(self):
        response = self.client.get(reverse("schema:schemas-list"))
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(len(response_json), 1)
        self.assertDictEqual(
            response_json[0], SchemaSerializer(self.schema).data
        )

    def test_retrieve(self):
        response = self.client.get(
            reverse("schema:schemas-detail", kwargs={"pk": 1})
        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(), SchemaSerializer(self.schema).data
        )

        # owned by another user isn't accessible
        response = self.client.get(
            reverse("schema:schemas-detail", kwargs={"pk": 2})
        )
        self.assertEqual(response.status_code, 404)

    def test_create(self):
        schema_data = {
            "name": "Citizens",
            "column_separator": "-",
            "quotechar": "!",
            "columns": [
                {
                    "type": "name",
                    "params": {"name": "Full name", "order": 1},
                },
                {
                    "type": "random_int",
                    "params": {"name": "Age", "order": 2, "min": 4, "max": 15},
                },
                {"type": "job", "params": {"name": "Job", "order": 3}},
            ],
        }

        response = self.client.post(
            reverse("schema:schemas-list"), data=schema_data, format="json"
        )
        self.assertEqual(response.status_code, 201)
        response_json = response.json()
        response_json.pop("id")
        self.assertDictEqual(response_json, schema_data)

    def test_create_with_invalid_data(self):
        schema_data = {
            "name": "Citizens",
            "column_separator": "-",
            "quotechar": "!@#",  # more than one char
            "columns": [
                # missed order
                {
                    "type": "name",
                    "params": {"name": "Full name"},
                },
                # min > max
                {
                    "type": "random_int",
                    "params": {"name": "Age", "order": 2, "min": 20, "max": 5},
                },
                # just fine
                {"type": "job", "params": {"name": "Job", "order": 3}},
                # incorrect type
                {"type": "nonexistent", "params": {"name": "Job", "order": 3}},
                # missed params
                {"type": "name"},
            ],
        }

        response = self.client.post(
            reverse("schema:schemas-list"), data=schema_data, format="json"
        )
        self.assertEqual(response.status_code, 400)

        self.assertDictEqual(
            response.json(),
            {
                "quotechar": [
                    "Ensure this field has no more than 1 characters."
                ],
                "columns": {
                    "0": {"params": {"order": ["This field is required."]}},
                    "1": {
                        "params": {
                            "__all__": ["Min must be less than max."],
                            "min": ["Min must be less than max."],
                            "max": ["Max must be greater than min."],
                        }
                    },
                    "3": {
                        "type": [
                            'Given column type "nonexistent" isn\'t exists.'
                        ]
                    },
                    "4": {"params": ["This field is required."]},
                },
            },
        )

    def test_update(self):
        schema_data_update = {
            "name": "Humans",
            "column_separator": "-",
            "quotechar": "!",
            "columns": [
                {
                    "type": "name",
                    "params": {"name": "Full name", "order": 1},
                },
                {
                    "type": "random_int",
                    "params": {"name": "Age", "order": 2, "min": 4, "max": 15},
                },
                {"type": "job", "params": {"name": "Job", "order": 3}},
            ],
        }

        response = self.client.put(
            reverse("schema:schemas-detail", kwargs={"pk": 1}),
            data=schema_data_update,
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), schema_data_update | {"id": 1})

        # can't update owned by another user
        response = self.client.put(
            reverse("schema:schemas-detail", kwargs={"pk": 2}),
            data=schema_data_update,
            format="json",
        )
        self.assertEqual(response.status_code, 404)

        # can't update non-existend
        response = self.client.put(
            reverse("schema:schemas-detail", kwargs={"pk": 3}),
            data=schema_data_update,
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_update_partial(self):
        schema_data_update = {
            "name": "Humans",
            "columns": [
                {"type": "job", "params": {"name": "Job", "order": 3}},
            ],
        }

        response = self.client.patch(
            reverse("schema:schemas-detail", kwargs={"pk": 1}),
            data=schema_data_update,
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertDictEqual(response_json, response_json | schema_data_update)

        # can't update owned by another user
        response = self.client.patch(
            reverse("schema:schemas-detail", kwargs={"pk": 2}),
            data=schema_data_update,
            format="json",
        )
        self.assertEqual(response.status_code, 404)

        # can't update non-existent
        response = self.client.patch(
            reverse("schema:schemas-detail", kwargs={"pk": 3}),
            data=schema_data_update,
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_delete(self):
        response = self.client.delete(
            reverse("schema:schemas-detail", kwargs={"pk": 1})
        )

        self.assertEqual(response.status_code, 204)
        with self.assertRaises(Schema.DoesNotExist):
            Schema.objects.get(id=1)

        # try to retrieve again, just to be sure.
        # maybe there will be some caching in the future
        response = self.client.get(
            reverse("schema:schemas-detail", kwargs={"pk": 1})
        )
        self.assertEqual(response.status_code, 404)

        # can't delete again
        response = self.client.delete(
            reverse("schema:schemas-detail", kwargs={"pk": 1})
        )
        self.assertEqual(response.status_code, 404)

        # can't delete owned by another user
        response = self.client.delete(
            reverse("schema:schemas-detail", kwargs={"pk": 2})
        )
        self.assertEqual(response.status_code, 404)


class TestDatasetViewSet(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="testuser", password="12345"
        )
        cls.schema = Schema.objects.create(
            **{
                "name": "People",
                "column_separator": ";",
                "quotechar": "!",
            },
            user=cls.user
        )
        cls.dataset = Dataset.objects.create(
            num_rows=10, schema=cls.schema, file="/tmp/testfile.csv"
        )

        # second set of user/schema to check filtering
        user2 = get_user_model().objects.create_user(
            username="testuser2", password="67890"
        )
        schema2 = Schema.objects.create(
            **{
                "name": "Creatures",
                "column_separator": ";",
                "quotechar": "!",
            },
            user=user2
        )
        Dataset.objects.create(
            num_rows=10, schema=schema2, file="/tmp/testfile2.csv"
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_urls_resolves(self):
        self.assertIs(
            resolve(
                reverse(
                    "schema:datasets-list", kwargs={"parent_lookup_schema": 1}
                )
            ).func.cls,
            views.DatasetViewSet,
        )
        self.assertIs(
            resolve(
                reverse(
                    "schema:datasets-detail",
                    kwargs={"parent_lookup_schema": 1, "pk": 1},
                )
            ).func.cls,
            views.DatasetViewSet,
        )
        self.assertIs(
            resolve(
                reverse(
                    "schema:datasets-generate",
                    kwargs={"parent_lookup_schema": 1},
                )
            ).func.cls,
            views.DatasetViewSet,
        )

    def test_is_auth_restricted(self):
        self.client.logout()

        response = self.client.get(
            reverse("schema:datasets-list", kwargs={"parent_lookup_schema": 1})
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.get(
            reverse(
                "schema:datasets-detail",
                kwargs={"parent_lookup_schema": 1, "pk": 1},
            )
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.post(
            reverse(
                "schema:datasets-generate", kwargs={"parent_lookup_schema": 1}
            )
        )
        self.assertEqual(response.status_code, 403)

    def test_list(self):
        response = self.client.get(
            reverse("schema:datasets-list", kwargs={"parent_lookup_schema": 1})
        )
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(len(response_json), 1)
        response_json[0]["file"] = response_json[0]["file"].split(
            "http://testserver"
        )[1]
        self.assertDictEqual(
            response_json[0], DatasetSerializer(self.dataset).data
        )

    def test_retrieve(self):
        response = self.client.get(
            reverse(
                "schema:datasets-detail",
                kwargs={"parent_lookup_schema": 1, "pk": 1},
            )
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertIn("file", response_json)
        response_json["file"] = response_json["file"].split(
            "http://testserver"
        )[1]
        self.assertDictEqual(
            response_json, DatasetSerializer(self.dataset).data
        )

        # owned by another user isn't accessible
        response = self.client.get(
            reverse(
                "schema:datasets-detail",
                kwargs={"parent_lookup_schema": 2, "pk": 2},
            )
        )
        self.assertEqual(response.status_code, 404)
