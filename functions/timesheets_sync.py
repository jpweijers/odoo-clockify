import logging
import os
import math
import time
from datetime import date, datetime, timedelta

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


def sync_timesheets(event=None, context=None):
    clockify_session = clockify.ClockifySession(
        CLOCKIFY_URL,
        CLOCKIFY_KEY,
        CLOCKIFY_WORKSPACE,
        CLOCKIFY_CLIENT_ID,
        CLOCKIFY_USER,
    )

    odoo_session = odoo.OdooSession(ODOO_BASE_URL, ODOO_LOGIN, ODOO_PASSWORD)

    start = date.today()
    end = start + timedelta(days=1)

    clockify_times = clockify_session.get_time_entries(start, end)

    odoo_times = odoo_session.get_time_entries(start, end)

    for project, tasks in clockify_times.items():
        for task, descriptions in dict(tasks).items():
            for description, duration in dict(descriptions).items():
                pid = int(project)
                tid = int(task)
                duration = odoo.seconds_to_hours(duration)
                odoo_entry = odoo_times.get(pid, {}).get(tid, {}).get(description, {})
                odoo_duration = odoo_entry.get("duration")
                odoo_entry_id = odoo_entry.get("id")

                if odoo_duration:
                    if odoo_duration == duration:
                        logging.info(
                            f"Correct time in odoo for: {project} - {task} - {description} - {duration}"
                        )
                    else:
                        updated_odoo_entry = odoo_session.update_time_entry(
                            odoo_entry_id, duration
                        )
                        if "error" not in updated_odoo_entry:
                            logging.info(
                                f"Updated time in odoo for: {project} - {task} - {description} - {duration}"
                            )
                        else:
                            logging.error(
                                f"Could not update time for: {project} - {task} - {description} - {duration}. Error: {updated_odoo_entry['error']}"
                            )
                else:
                    new_odoo_entry = odoo_session.create_time_entry(
                        project,
                        task,
                        description,
                        duration,
                        start.isoformat()[:10],
                    )
                    if "error" not in new_odoo_entry:
                        logging.info(
                            f"Created time in odoo for: {project} - {task} - {description} - {duration}"
                        )
                    else:
                        logging.error(
                            f"Could not create time for: {project} - {task} - {description} - {duration}. Error: {new_odoo_entry['error']}"
                        )


if __name__ == "__main__":
    result = sync_timesheets()
    print(result)
