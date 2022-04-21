import logging
import json
import os
from datetime import date, timedelta

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


# remove root logging handler so that logging works with cloudwatch
logging.root.handlers = []
logging.basicConfig(level=logging.INFO)


def deleted(event={}, context={}):
    CLOCKIFY_WEBHOOK_SIGNATURE_DELETED = os.environ[
        "CLOCKIFY_WEBHOOK_SIGNATURE_STOPPED"
    ]
    logging.info(f"event: {event}")
    return {"Accepted": True}


def stopped(event={}, context={}):
    CLOCKIFY_WEBHOOK_SIGNATURE_STOPPED = os.environ[
        "CLOCKIFY_WEBHOOK_SIGNATURE_STOPPED"
    ]
    logging.info(f"Event: {event}")
    if all(k in event for k in ["body", "headers"]):
        signature = event["headers"].get("clockify-signature")
        body = json.loads(event["body"])
        if signature == CLOCKIFY_WEBHOOK_SIGNATURE:
            description = body.get("description")
            project = body.get("project")
            task = body.get("task")
            if (
                description
                and project
                and project["clientId"] == CLOCKIFY_CLIENT_ID
                and task
            ):
                clockify_session = clockify.ClockifySession(
                    CLOCKIFY_URL,
                    CLOCKIFY_KEY,
                    CLOCKIFY_WORKSPACE,
                    CLOCKIFY_CLIENT_ID,
                    CLOCKIFY_USER,
                )
                odoo_project_id = clockify.odoo_id_from_note(project.get("note"))
                odoo_task_id = clockify.odoo_id_from_task(task.get("name"))

                clockify_task_id = task.get("id")
                start = date.fromisoformat(body["timeInterval"]["start"][:10])
                end = start + timedelta(days=1)
                query = {
                    "description": description,
                    "hydrated": "true",
                    "task": clockify_task_id,
                }
                entries_same_day = clockify_session.get_time_entries(start, end, query)
                duration = entries_same_day[odoo_project_id][odoo_task_id][description]

                odoo_session = odoo.OdooSession(
                    ODOO_BASE_URL, ODOO_LOGIN, ODOO_PASSWORD
                )
                odoo_entry_same_day = odoo_session.get_same_day_time_entries(
                    odoo_project_id, odoo_task_id, description, start, end
                )

                duration = odoo.seconds_to_hours(duration)
                odoo_duration = odoo_entry_same_day["unit_amount"]
                if odoo_entry_same_day:
                    if duration != odoo_duration:
                        entry_id = odoo_entry_same_day["id"]
                        updated_odoo_entry = odoo_session.update_time_entry(
                            entry_id, duration
                        )
                        if "error" not in updated_odoo_entry:
                            logging.info(
                                f"Updated time in odoo for: {project['name']} - {task['name']} - {description} - {duration}"
                            )
                        else:
                            logging.error(
                                f"Could not Update time for: {project['name']} - {task['name']} - {description} - {duration}. Error: {updated_odoo_entry['error']}"
                            )
                    else:
                        logging.info(
                            f"Time not changed for: {project['name']} - {task['name']} - {description} - {duration}"
                        )
                else:
                    new_odoo_entry = odoo_session.create_time_entry(
                        odoo_project_id, odoo_task_id, description, duration
                    )
                    if "error" not in new_odoo_entry:
                        logging.info(
                            f"Created time in odoo for: {project['name']} - {task['name']} - {description} - {duration}"
                        )
                    else:
                        logging.error(
                            f"Could not Create time for: {project['name']} - {task['name']} - {description} - {duration}. Error: {new_odoo_entry['error']}"
                        )
                return {"Accepted": True}
        return {"Accepted": False}


if __name__ == "__main__":
    from tmp.testdata import test_event_update

    result = stopped(test_event_update, {})
    print(result)
