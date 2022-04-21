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

odoo_session = None
clockify_session = None


def updated(event={}, context={}):
    global odoo_session

    CLOCKIFY_WEBHOOK_SIGNATURE = os.environ["CLOCKIFY_WEBHOOK_SIGNATURE_UPDATED"]

    logging.info(f"event: {event}")

    if request_is_signed(event, CLOCKIFY_WEBHOOK_SIGNATURE):
        clockify_timesheet = get_clockify_timesheets(event)

        odoo_pid, odoo_tid, description, start, end, duration = clockify_timesheet

        odoo_session = odoo.OdooSession(ODOO_BASE_URL, ODOO_LOGIN, ODOO_PASSWORD)
        odoo_entry = odoo_session.get_same_day_time_entries(
            odoo_pid, odoo_tid, description, start, end
        )

        duration = odoo.seconds_to_hours(duration)
        if odoo_entry:
            odoo_duration = odoo_entry["unit_amount"]
            if duration != odoo_duration:
                update_odoo_timesheet(odoo_entry["id"], duration)
            else:
                logging.info(
                    f"Time not changed for: {odoo_pid} - {odoo_tid} - {description} - {duration}"
                )
        else:
            create_odoo_timesheet(odoo_pid, odoo_tid, description, duration)

        return {"Accepted": True}


def update_odoo_timesheet(entry_id, duration):
    global odoo_session

    updated_odoo_entry = odoo_session.update_time_entry(entry_id, duration)
    if "error" not in updated_odoo_entry:
        logging.info(
            f"Updated time in odoo for: {project['name']} - {task['name']} - {description} - {duration}"
        )
    else:
        logging.error(
            f"Could not Update time for: {project['name']} - {task['name']} - {description} - {duration}. Error: {updated_odoo_entry['error']}"
        )


def create_odoo_timesheet(odoo_project_id, odoo_task_id, description, duration):
    global odoo_session

    new_odoo_entry = odoo_session.create_time_entry(
        odoo_project_id, odoo_task_id, description, duration
    )
    if "error" not in new_odoo_entry:
        logging.info(
            f"Created time in odoo for: {odoo_project_id} - {odoo_task_id} - {description} - {duration}"
        )
    else:
        logging.error(
            f"Could not Create time for: {odoo_project_id} - {odoo_task_id} - {description} - {duration}. Error: {new_odoo_entry['error']}"
        )


def request_is_signed(event, signature):
    if all(k in event for k in ["body", "headers"]):
        signed = signature == event["headers"].get("clockify-signature")
        if signed:
            return True
    return False


def create_clockify_session():
    return clockify.ClockifySession(
        CLOCKIFY_URL,
        CLOCKIFY_KEY,
        CLOCKIFY_WORKSPACE,
        CLOCKIFY_CLIENT_ID,
        CLOCKIFY_USER,
    )


def get_clockify_timesheets(event):
    body = json.loads(event["body"])
    description = body.get("description")
    project = body.get("project")
    task = body.get("task")
    if description and project and project["clientId"] == CLOCKIFY_CLIENT_ID and task:

        odoo_pid = clockify.odoo_id_from_note(project.get("note"))
        odoo_tid = clockify.odoo_id_from_task(task.get("name"))
        clockify_task_id = task.get("id")

        clockify_session = create_clockify_session()

        start = date.fromisoformat(body["timeInterval"]["start"][:10])
        end = start + timedelta(days=1)
        query = {
            "description": description,
            "hydrated": "true",
            "task": clockify_task_id,
        }

        duration = (
            clockify_session.get_time_entries(start, end, query)
            .get(odoo_pid, {})
            .get(odoo_tid, {})
            .get(description)
        )

        return (odoo_pid, odoo_tid, description, start, end, duration)


def manual(event={}, context={}):
    CLOCKIFY_WEBHOOK_SIGNATURE = os.environ["CLOCKIFY_WEBHOOK_SIGNATURE_MANUAL"]
    logging.info(f"event: {event}")
    return {"Accepted": True}


def deleted(event={}, context={}):
    CLOCKIFY_WEBHOOK_SIGNATURE = os.environ["CLOCKIFY_WEBHOOK_SIGNATURE_DELETED"]
    logging.info(f"event: {event}")
    return {"Accepted": True}


def stopped(event={}, context={}):
    global odoo_session
    CLOCKIFY_WEBHOOK_SIGNATURE = os.environ["CLOCKIFY_WEBHOOK_SIGNATURE_STOPPED"]
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

    result = updated(test_event_update, {})
    print(result)
