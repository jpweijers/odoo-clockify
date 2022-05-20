import json
import logging
import os
import time
import asyncio

from clockify import session
from clockify.model.project_model import Project
from clockify.model.task_model import Task
from odoo_api import odoo

ODOO_BASE_URL = os.environ["ODOO_URL"]
ODOO_LOGIN = os.environ["ODOO_LOGIN"]
ODOO_PASSWORD = os.environ["ODOO_PASSWORD"]

CLOCKIFY_URL = os.environ["CLOCKIFY_URL"]
CLOCKIFY_KEY = os.environ["CLOCKIFY_KEY"]
CLOCKIFY_WORKSPACE = os.environ["CLOCKIFY_WORKSPACE"]
CLOCKIFY_CLIENT_ID = os.environ["CLOCKIFY_CLIENT_ID"]
CLOCKIFY_USER = os.environ["CLOCKIFY_USER"]

execution_time = time.perf_counter()

# remove root logging handler so that logging works with cloudwatch
logging.root.handlers = []
logging.basicConfig(level=logging.INFO)


def handler(event=None, context=None):
    # Get Odoo Projects
    logging.info("Retrieving Odoo Projects")
    odoo_session = odoo.OdooSession(ODOO_BASE_URL, ODOO_LOGIN, ODOO_PASSWORD)
    odoo_projects = asyncio.run(odoo_session.get_projects_with_tasks())
    logging.info(f"Odoo Projects retrieved in {timer()}")

    logging.info("Retrieving Odoo Projects")
    clockify_session = session.ClockifySession(CLOCKIFY_KEY)
    clockify_projects = clockify_session.get_projects(CLOCKIFY_WORKSPACE)
    logging.info(f"Clockify Projects retrieved in {timer()}")

    clockify_projects = {p.name: p for p in clockify_projects}

    # Determine projects to create and projects to archive
    op = set(odoo_projects)
    # input(odoo_projects)
    cp = set(clockify_projects)

    to_create = {p: odoo_projects[p] for p in op if p not in cp}
    to_archive = {p: clockify_projects[p].id_ for p in cp if p not in op}
    #    # Create projects
    logging.info(f"Creating {len(to_create)} projects")
    if to_create:
        for k, v in to_create.items():
            project = Project(name=k, workspace_id=CLOCKIFY_WORKSPACE, client_id=CLOCKIFY_CLIENT_ID, note=f"odoo_id={v['id']}")
            project = clockify_session.create_project(project)
            for t in v["tasks"]:
                for name, odoo_id in t.items():
                    task = Task(name=f"{name} #{odoo_id}", project_id=project.id_)
                    task = clockify_session.create_task(CLOCKIFY_WORKSPACE, task=task)


    # Archive projects
    logging.info(f"Archiving {len(to_archive)} projects")
    if to_archive:
        #clockify_session.archive_projects(to_archive)
        pass

    logging.info(f"Updated Clockify projects and tasks in {timer()} seconds")


def timer():
    return f"{time.perf_counter() - execution_time} seconds"


if __name__ == "__main__":
    result = handler()
    print(result)
