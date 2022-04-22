import json
import logging
import re
import math
from datetime import datetime, date
from collections import defaultdict

import requests


class ClockifySession:
    def __init__(self, url, key, workspace, client, user):
        self.url = f"{url}/workspaces/{workspace}"
        self.key = key
        self.client = client
        self.user = user

    def get_projects(self, query={}):
        url = f"{self.url}/projects"
        default_query = {
            "archived": "false",
            "page-size": "100",
            "clients": self.client,
        }
        query = {**default_query, **query}
        headers = {"x-api-key": self.key}
        response = requests.get(url, headers=headers, params=query)
        projects = response.json()
        return {p["name"]: p for p in projects}

    def create_projects(self, projects=[]):
        for name, project in projects.items():
            url = f"{self.url}/projects"
            payload = {
                "name": name,
                "clientId": self.client,
                "isPublic": "false",
                "note": f"odoo_id={project['id']}",
            }
            response = requests.post(url, json=payload, headers=self._headers())

            if response.status_code == 201:
                logging.info(f'{response.status_code} - Project "{name}" created.')
                project_id = response.json().get("id")

                for tasks in project["tasks"]:
                    for task, id in tasks.items():
                        self.create_task(project_id, task, id)

            else:
                logging.error(f'{response.status_code} - Error: "{response.text}"')

    def create_task(self, project_id, task, id):
        url = f"{self.url}/projects/{project_id}/tasks"
        payload = {"name": f"{task} #{id}", "status": "ACTIVE"}
        response = requests.post(url, json=payload, headers=self._headers())

        if response.status_code == 201:
            logging.info(f'{response.status_code} - Task "{task} #{id}" created.')
        else:
            logging.error(f'{response.status_code} - Error: "{response.text}"')

    def archive_projects(self, projects=[]):
        for project, id in projects.items():
            url = f"{self.url}/projects/{id}"
            payload = {"archived": True}
            response = requests.put(url, json=payload, headers=self._headers())
            if response.status_code == 200:
                logging.info(f'200 - Project "{project}" archived')

    def get_time_entries(self, start, end, query={}):
        start = f"{start.isoformat()}T00:00:00Z"
        end = f"{end.isoformat()}T00:00:00Z"
        url = f"{self.url}/user/{self.user}/time-entries"
        query = {
            **{"start": f"{start}", "end": f"{end}", "hydrated": "true"},
            **query,
        }
        response = requests.get(url, params=query, headers=self._headers())

        entries = response.json()

        grouped = {}
        for entry in entries:
            description = entry["description"]
            if entry["project"] and entry["task"]:
                pid = odoo_id_from_note(entry.get("project").get("note", None))
                tid = odoo_id_from_task(entry.get("task").get("name"))
                start = entry["timeInterval"]["start"]
                end = entry["timeInterval"]["end"]
                if pid and tid and start and end:
                    duration = calculate_duration(start, end)
                    if pid in grouped:
                        if tid in grouped[pid]:
                            if description in grouped[pid][tid]:
                                grouped[pid][tid][description] += duration
                            else:
                                grouped[pid][tid][description] = duration
                        else:
                            grouped[pid] = {
                                **grouped[pid],
                                **{tid: {description: duration}},
                            }

                    else:
                        grouped = {**grouped, **{pid: {tid: {description: duration}}}}

        return dict(grouped)

    def _headers(self):
        return {"x-api-key": self.key}


def odoo_id_from_note(note):
    return int(re.search(r"odoo_id=(.*)", note)[1])


def odoo_id_from_task(task):
    return int(re.search(r"#(.*)", task)[1])


def calculate_duration(start, end):
    s = datetime.fromisoformat(start[:-1])
    e = datetime.fromisoformat(end[:-1])
    return (e - s).total_seconds()


def date_to_timestamp(date: date):
    return f"{date.isoformat()}T00:00:00Z"
