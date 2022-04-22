import json
import logging
import os
import time
import asyncio

import clockify.clockify as clockify
import odoo.odoo as odoo

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
    clockify_session = clockify.ClockifySession(
        CLOCKIFY_URL,
        CLOCKIFY_KEY,
        CLOCKIFY_WORKSPACE,
        CLOCKIFY_CLIENT_ID,
        CLOCKIFY_USER,
    )
    clockify_projects = clockify_session.get_projects()
    logging.info(f"Clockify Projects retrieved in {timer()}")

    # Determine projects to create and projects to archive
    op = set(odoo_projects)
    cp = set(clockify_projects)

    to_create = {p: odoo_projects[p] for p in op if p not in cp}
    to_archive = {p: clockify_projects[p]["id"] for p in cp if p not in op}

    # Create projects
    logging.info(f"Creating {len(to_create)} projects")
    if to_create:
        clockify_session.create_projects(to_create)

    # Archive projects
    logging.info(f"Archiving {len(to_archive)} projects")
    if to_archive:
        clockify_session.archive_projects(to_archive)

    logging.info(f"Updated Clockify projects and tasks in {timer()} seconds")


def timer():
    return f"{time.perf_counter() - execution_time} seconds"


if __name__ == "__main__":
    result = handler()
    print(result)
