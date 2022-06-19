from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Dataset, NameColumn, RandomIntColumn, Schema
from ..tasks import generate_data


class TestRunGenerateDataTask(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(  # type: ignore
            username="testuser",
            password="testpass",
        )
        cls.schema = Schema.objects.create(name="Test schema", user=cls.user)
        NameColumn.objects.create(name="Full name", order=1, schema=cls.schema)
        RandomIntColumn.objects.create(
            name="Age", min=15, max=80, order=2, schema=cls.schema
        )

    def create_dataset(self):
        return Dataset.objects.create(num_rows=10, schema=self.schema)

    def test_run_locally_and_get_dataset_file_set(self):
        dataset = self.create_dataset()
        self.assertFalse(dataset.file)

        generate_data.run(dataset.id)
        dataset.refresh_from_db()
        self.assertTrue(dataset.file)

    def test_resulting_filenames_are_different(self):
        dataset_1 = self.create_dataset()
        generate_data.run(dataset_1.id)
        dataset_1.refresh_from_db()

        dataset_2 = self.create_dataset()
        generate_data.run(dataset_2.id)
        dataset_2.refresh_from_db()

        self.assertNotEqual(dataset_1.file.name, dataset_2.file.name)

    # @skipUnless(settings.TEST_INTEGRATION, "Integration tests are disabled")
    # def test_it_runs_as_a_worker(self):
    #     generate_data.delay(self.dataset.id)
    #     sleep(5) # TODO: replace with some celery assertion
    #     self.dataset.refresh_from_db()
    #     self.assertTrue(self.dataset.file)
