import json
from tests.config import TestCase
from tests.config import CLOCKIFY_CLIENT_ID


class TestClockify(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = cls.create_clockify_session()
        cls.created_projects = {}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.session.archive_projects(cls.created_projects)
        cls.session.delete_projects(cls.created_projects)

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
            with self.assertLogs() as captured:
                result = self.session.create_projects(project)
                self.assertGreater(len(result), 0)
                new_project = result[0]
                self.assertEqual(new_project["error"], False)
                self.created_projects[name] = new_project["id"]

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
            self.created_projects[result["name"]] = result["id"]


class TestCreateProject(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.created_projects = {}
        cls.session = cls.create_clockify_session()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.session.archive_projects(cls.created_projects)
        cls.session.delete_projects(cls.created_projects)
        pass

    def _test_archive_projects(self):
        names = ["test archive 1", "test archive 2", "test archive 3"]

        for name in names:
            project = {name: {"id": 123, "tasks": [{"task 1": 123}, {"task 2": 123}]}}
            id = self.session.create_projects(project)["id"]
            with self.assertLogs() as captured:
                archived_project = self.session.archive_projects({name: id})
            self.archived_projects[name] = id

            self.assertEqual(archived_project["error"], False)
            self.assertEqual(
                captured.records[0].getMessage(),
                f'200 - Project "{name}" archived',
            )
        # self.fail(json.dumps(self.created_projects))

    def test_createprojects_fail(self):
        name = "test fail 1"
        project = {name: {"id": 123, "tasks": [{"task 1": 123}, {"task 2": 123}]}}
        new_project = self.session.create_projects(project)
        self.created_projects[name] = new_project["id"]
        with self.assertLogs() as captured:
            new_project = self.session.create_projects(project)
            self.assertEqual(new_project, {"error": True})

        self.assertEqual(captured.records[0].levelname, "ERROR")


class TestArchiveProject(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.session = cls.create_clockify_session()
        cls.archived_projects = {}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.session.delete_projects(cls.archived_projects)

    def test_archive_projects(self):
        names = ["test archive 1", "test archive 2", "test archive 3"]

        for name in names:
            project = {name: {"id": 123, "tasks": [{"task 1": 123}, {"task 2": 123}]}}
            id = self.session.create_projects(project)["id"]
            with self.assertLogs() as captured:
                archived_project = self.session.archive_projects({name: id})
            self.archived_projects[name] = id

            self.assertEqual(archived_project["error"], False)
            self.assertEqual(
                captured.records[0].getMessage(),
                f'200 - Project "{name}" archived',
            )


class TestDeleteProject(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = cls.create_clockify_session()

    def test_delete_projects(self):
        projects = ["test delete 1"]
        for project in projects:
            new_project = self.session.create_projects(
                {project: {"id": 123, "tasks": [{"task 1": 123}, {"task 2": 123}]}}
            )
            self.session.archive_projects({project: new_project["id"]})
            with self.assertLogs() as captured:
                deleted_project = self.session.delete_projects(
                    {project: new_project["id"]}
                )

            self.assertEqual(deleted_project, {"error": False})
            self.assertEqual(
                captured.records[0].getMessage(), f'200 - Project "{project}" deleted'
            )


class TestCreateTask(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.session = cls.create_clockify_session()
        cls.created_projects = {}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.session.delete_projects(cls.created_projects)

    def test_create_tasks(self):
        name = "test tasks 1"
        project = {name: {"id": 123, "tasks": [{"task 1": 123}, {"task 2": 123}]}}
        pid = self.session.create_projects(project)["id"]
        self.created_projects[name] = pid

        for tasks in project[name]["tasks"]:
            for task, id in tasks.items():
                tid = task[task]
                new_task = self.session.create_task(pid, task, tid)

                self.assertIsNotNone(new_task["id"])
                self.assertNotEqual(new_task, {"error": True})
