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

odoo_session = odoo.OdooSession(ODOO_BASE_URL, ODOO_LOGIN, ODOO_PASSWORD)
clockify_session = clockify.ClockifySession(
    CLOCKIFY_URL, CLOCKIFY_KEY, CLOCKIFY_WORKSPACE, CLOCKIFY_CLIENT_ID, CLOCKIFY_USER
)


class TimesheetLogger:
    def __init__(self, project, task, description, duration):
        self.project = project
        self.task = task
        self.description = description
        self.duration = duration

    def _info(self, msg):
        return f"{msg} - Timesheet: {self.project} - {self.task} - {self.description} - {self.duration}"

    def _error(self, msg, err):
        return f"{self.info(msg)} Error: {err}"

    def info(self, msg):
        logging.info(self._info(msg))

    def error(self, msg, err):
        logging.info(self.error(msg, err))


t_logger: TimesheetLogger


def updated(event={}, context={}):
    CLOCKIFY_WEBHOOK_SIGNATURE = os.environ["CLOCKIFY_WEBHOOK_SIGNATURE_UPDATED"]

    return process_request(event, CLOCKIFY_WEBHOOK_SIGNATURE)


def stopped(event={}, context={}):
    CLOCKIFY_WEBHOOK_SIGNATURE = os.environ["CLOCKIFY_WEBHOOK_SIGNATURE_STOPPED"]

    return process_request(event, CLOCKIFY_WEBHOOK_SIGNATURE)


def deleted(event={}, context={}):
    CLOCKIFY_WEBHOOK_SIGNATURE = os.environ["CLOCKIFY_WEBHOOK_SIGNATURE_DELETED"]

    return process_request(event, CLOCKIFY_WEBHOOK_SIGNATURE)


def manual(event={}, context={}):
    CLOCKIFY_WEBHOOK_SIGNATURE = os.environ["CLOCKIFY_WEBHOOK_SIGNATURE_MANUAL"]

    return process_request(event, CLOCKIFY_WEBHOOK_SIGNATURE)


def process_request(event, signature):
    global t_logger

    logging.info(f"event: {event}")
    if request_is_signed(event, signature):
        clockify_timesheet = get_clockify_timesheets(event)

        (
            odoo_pid,
            odoo_tid,
            description,
            start,
            end,
            duration,
        ) = clockify_timesheet

        odoo_entry = odoo_session.get_same_day_time_entries(
            odoo_pid, odoo_tid, description, start, end
        )
        duration = odoo.seconds_to_hours(duration)
        t_logger.duration = duration

        if odoo_entry:
            odoo_duration = odoo_entry["unit_amount"]
            if duration == 0:
                delete_odoo_timesheet(odoo_entry["id"])
            elif duration != odoo_duration:
                update_odoo_timesheet(odoo_entry["id"], duration, description)
            else:
                t_logger.info("Time not changed")
        else:
            create_odoo_timesheet(odoo_pid, odoo_tid, description, duration, start)

        return {"Accepted": True}

    return {"Accepted": False}


def update_odoo_timesheet(entry_id, duration, description):
    global t_logger

    updated_odoo_entry = odoo_session.update_time_entry(entry_id, duration)
    if "error" not in updated_odoo_entry:
        t_logger.info(f"Updated time in Odoo")
    else:
        t_logger.error(f"Could not Update time in Odoo", updated_odoo_entry["error"])


def create_odoo_timesheet(odoo_project_id, odoo_task_id, description, duration, start):
    global t_logger

    new_odoo_entry = odoo_session.create_time_entry(
        odoo_project_id, odoo_task_id, description, duration, start
    )
    if "error" not in new_odoo_entry:
        t_logger.info("Created time in Odoo")
    else:
        t_logger.error("Could not create time in Odoo", new_odoo_entry["error"])


def delete_odoo_timesheet(entry_id):
    global t_logger

    deleted_odoo_entry = odoo_session.unlink_time_entry(entry_id)
    if "error" not in deleted_odoo_entry:
        t_logger.info("Deleted time entry from Odoo")
    else:
        t_logger.info("Could not delete time entry from Odoo")


def request_is_signed(event, signature):
    if all(k in event for k in ["body", "headers"]):
        signed = signature == event["headers"].get("clockify-signature")
        if signed:
            return True
    return False


def get_clockify_timesheets(event):
    global t_logger

    body = json.loads(event["body"])
    description = body.get("description")
    project = body.get("project")
    task = body.get("task")
    if description and project and project["clientId"] == CLOCKIFY_CLIENT_ID and task:

        odoo_pid = clockify.odoo_id_from_note(project.get("note"))
        odoo_tid = clockify.odoo_id_from_task(task.get("name"))

        clockify_task_id = task.get("id")

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
            .get(description, 0)
        )

        t_logger = TimesheetLogger(project["name"], task["name"], description, duration)

        return (
            odoo_pid,
            odoo_tid,
            description,
            start,
            end,
            duration,
        )


if __name__ == "__main__":
    from tmp.testdata import test_event_update, test_event_stopped, test_event_delete

    # result = updated(test_event_update, {})
    # result = stopped(test_event_stopped, {})
    result = deleted(test_event_delete, {})
    print(result)
