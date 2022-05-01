import json
import logging
import math
import re
from datetime import datetime

import boto3
from clockify.model.time_entry_model import TimeEntry
from odoo_api.odoo import OdooSession
from config import *


logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

odoo_session = OdooSession(ODOO_URL, ODOO_LOGIN, ODOO_PASSWORD)


def main(event: dict = {}, context: dict = {}) -> None:

    logger.info(f"Event: {json.dumps(event)}")

    for record in event["Records"]:
        try:
            body = json.loads(record["body"])

            odoo_pid = odoo_id_from_note(body.get("project", {}).get("note"))
            odoo_tid = odoo_id_from_task(body.get("task", {}).get("name"))

            clockify_time_entry = TimeEntry(**body)

            odoo_id = (
                table.get_item(Key={"clockify_id": clockify_time_entry.id_})
                .get("Item", {})
                .get("odoo_id")
            )

            sender_id = record["attributes"]["SenderId"]

            if "deleted-producer" in sender_id:
                logger.info(
                    f"Timesheet to delete odooId: {odoo_id} clockify data: {clockify_time_entry}"
                )
                if odoo_id:
                    odoo_session.unlink_data("account.analytic.line", [[odoo_id]])
                    logger.info("Timesheet deleted from odoo")
                else:
                    logger.info("Timesheet not in Odoo")

            else:
                # created or updated timesheet
                duration = odoo_duration_from_start_end(
                    clockify_time_entry.time_interval.start,
                    clockify_time_entry.time_interval.end,
                )

                if all([odoo_id, odoo_pid, odoo_tid]):
                    logger.info("Timesheet already exists in Odoo")

                    odoo_data = {
                        "project_id": odoo_pid,
                        "task_id": odoo_tid,
                        "date": clockify_time_entry.time_interval.start[:10],
                        "unit_amount": duration,
                        "name": clockify_time_entry.description,
                    }
                    odoo_session.update_data(
                        "account.analytic.line", [[odoo_id], odoo_data]
                    )
                    logger.info(
                        f"Updated timesheet with odooId: {odoo_id} and clockify data: {clockify_time_entry}"
                    )

                elif all([odoo_pid, odoo_tid]):
                    # not yet in odoo
                    print(f"Timesheet to add {clockify_time_entry}")
                    odoo_data = {
                        "validated": False,
                        "project_id": odoo_pid,
                        "task_id": odoo_tid,
                        "user_id": odoo_session.user_id,
                        "employee_id": odoo_session.employee_id,
                        "date": clockify_time_entry.time_interval.start[:10],
                        "unit_amount": duration,
                        "name": clockify_time_entry.description,
                    }
                    result = odoo_session.create_data(
                        "account.analytic.line", [odoo_data]
                    )
                    odoo_id = result.get("result")
                    table.put_item(
                        Item={
                            "clockify_id": clockify_time_entry.id_,
                            "odoo_id": odoo_id,
                        }
                    )
                    print(
                        f"Created timesheet with odooId: {odoo_id} and clockify data: {clockify_time_entry}"
                    )

        except ValueError as e:
            raise ValueError(f"Failed to process record: {e}")


def odoo_id_from_note(note: str) -> int:
    match = re.search(r"odoo_id=(\d+)$", note)
    if match:
        return int(match[1])


def odoo_id_from_task(task: str) -> int:
    match = re.search(r"#(\d+)$", task)
    if match:
        return int(match[1])


def odoo_duration_from_start_end(start: str, end: str):
    start = datetime.fromisoformat(start[:-1])
    end = datetime.fromisoformat(end[:-1])
    seconds = (end - start).total_seconds()
    hours = seconds / 3600
    return math.ceil(hours * 4) / 4
