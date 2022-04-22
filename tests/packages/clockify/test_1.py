from src.packages.clockify import clockify

from tests.config import TestCase
from tests.config import CLOCKIFY_CLIENT_ID


class TestClockify(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = cls.create_clockify_session()
        cls.created_projects = []
        cls.archived_projects = []

    @classmethod
    def tearDownClass(cls) -> None:
        cls.session.archive_projects(cls.created_projects)
        cls.session.delete_projects(cls.created_projects + cls.archived_projects)

    def test_get_projects(self):
        query = {"clients": CLOCKIFY_CLIENT_ID}
        result = self.session.get_projects(query)
        self.assertEqual(type(result), dict)
        self.assertGreater(len(result), 0)

    def test_get_projects_fail(self):
        query = {"clients": "nonexistent client"}
        result = self.session.get_projects(query)
        self.assertEqual(result, {})
        self.assertEqual(len(result), 0)

    def test_create_projects(self):
        names = ["test create 1", "test create 2", "test create 3"]

        for name in names:
            project = {name: {"id": 123}}
            result = self.session.create_projects(project)
            self.assertGreater(len(result), 0)
            new_project = result[0]
            self.assertEqual(new_project["error"], False)
            self.created_projects.append(new_project["id"])

    def test_create_multiple_projects_at_once(self):
        names = [
            "test create multiple 1",
            "test create multiple 2",
            "test create multiple 3",
        ]
        projects = {n: {"id": 123} for n in names}
        results = self.session.create_projects(projects)
        self.assertGreater(len(results), 0)
        for result in results:
            self.assertEqual(result["error"], False)
            self.created_projects.append(result["id"])

    def test_create_tasks(self):
        project = {"test create task 1": {"id": 123}}
        project_id = self.session.create_projects(project)[0]["id"]
        self.created_projects.append(project_id)
        tasks = [
            {"project_id": project_id, "task": "task 1"},
            {"project_id": project_id, "task": "task 2"},
            {"project_id": project_id, "task": "task 3"},
        ]
        results = self.session.create_tasks(tasks)
        self.assertGreater(len(results), 0)
        for result in results:
            self.assertEqual(result["error"], False)

    def test_archive_projects(self):
        names = [
            "test archive 1",
            "test archive 2",
            "test archive 3",
        ]
        projects = {n: {"id": 123} for n in names}
        results = self.session.create_projects(projects)
        project_ids = [r["id"] for r in results]

        results = self.session.archive_projects(project_ids)
        self.assertGreater(len(results), 0)
        for result in results:
            self.assertEqual(result["error"], False)

        self.archived_projects += project_ids

    def test_delete_projects(self):
        names = [
            "test delete 1",
            "test delete 2",
            "test delete 3",
        ]
        projects = {n: {"id": 123} for n in names}
        results = self.session.create_projects(projects)
        project_ids = [r["id"] for r in results]

        self.session.archive_projects(project_ids)

        results = self.session.delete_projects(project_ids)

        self.assertGreater(len(results), 0)
        for result in results:
            self.assertEqual(result["error"], False)

    def test_get_odoo_id_from_note(self):
        notes = {
            "odoo_id=123": 123,
            "odoo_id=321": 321,
            "odoo_id=1234123413241234": 1234123413241234,
            "odoo_id=": None,
            "=234": None,
            "odoo_id=123pizza": None,
        }
        for note, expected_result in notes.items():
            odoo_id = clockify.odoo_id_from_note(note)
            self.assertEqual(odoo_id, expected_result)

    def test_odoo_id_from_task(self):
        tasks = {
            "Work #1234": 1234,
            "Sleep #34214321": 34214321,
            "Eat #13241234sdf": None,
            "Code #1234  1324": None,
            "Vacation #1": 1,
            "Play #3414": 3414,
        }
        for task, expected_result in tasks.items():
            odoo_id = clockify.odoo_id_from_task(task)
            self.assertEqual(odoo_id, expected_result)
