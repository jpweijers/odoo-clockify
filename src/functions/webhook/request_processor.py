import logging
import json
from datetime import date, timedelta

from logger import TimesheetLogger
import src.packages.odoo.odoo as odoo
import src.packages.clockify.clockify as clockify

import config


odoo_session = odoo.OdooSession(
    config.ODOO_BASE_URL, config.ODOO_LOGIN, config.ODOO_PASSWORD
)
clockify_session = clockify.ClockifySession(
    config.CLOCKIFY_URL,
    config.CLOCKIFY_KEY,
    config.CLOCKIFY_WORKSPACE,
    config.CLOCKIFY_CLIENT_ID,
    config.CLOCKIFY_USER,
)

t_logger: TimesheetLogger


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
        elif duration > 0:
            create_odoo_timesheet(odoo_pid, odoo_tid, description, duration, start)

        return {"Accepted": True}

    return {"Accepted": False}


def update_odoo_timesheet(entry_id, duration, description):
    global t_logger

    updated_odoo_entry = odoo_session.update_time_entry(entry_id, duration)
    if "error" not in updated_odoo_entry:
        t_logger.info(f"Updated time in Odoo")
    else:
        error = updated_odoo_entry["error"]
        t_logger.error(f"Could not Update time in Odoo", error)


def create_odoo_timesheet(odoo_project_id, odoo_task_id, description, duration, start):
    global t_logger

    new_odoo_entry = odoo_session.create_time_entry(
        odoo_project_id, odoo_task_id, description, duration, start
    )
    if "error" not in new_odoo_entry:
        t_logger.info("Created time in Odoo")
    else:
        error = new_odoo_entry["error"]
        t_logger.error("Could not create time in Odoo", error)


def delete_odoo_timesheet(entry_id):
    global t_logger

    deleted_odoo_entry = odoo_session.unlink_time_entry(entry_id)
    if "error" not in deleted_odoo_entry:
        t_logger.info("Deleted time entry from Odoo")
    else:
        error = delete_odoo_timesheet["error"]
        t_logger.error("Could not delete time entry from Odoo", error)


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
    if (
        description
        and project
        and project["clientId"] == config.CLOCKIFY_CLIENT_ID
        and task
    ):

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
