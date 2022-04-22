import logging
import re
from datetime import datetime, date
from collections import defaultdict

import requests


class ClockifySession:
    def __init__(self, url, key, workspace, client, user):
        self.url = f"{url}/workspaces/{workspace}"
        self.headers = {"x-api-key": key}
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
        response = requests.get(url, headers=self.headers, params=query)
        projects = response.json()
        return {p["name"]: p for p in projects}

    def create_projects(self, projects={}):
        result = []
        for name, project in projects.items():
            url = f"{self.url}/projects"
            payload = {
                "name": name,
                "clientId": self.client,
                "isPublic": "false",
                "note": f"odoo_id={project['id']}",
            }
            response = requests.post(url, json=payload, headers=self.headers)

            if response.status_code == 201:
                msg = f'{response.status_code} - Project "{name}" created.'
                logging.info(msg)
                result.append({**response.json(), **{"error": False, "message": msg}})

            else:
                msg = f'{response.status_code} - Error: "{response.text}"'
                logging.error(msg)
                result.append({"error": True, "message": msg})
        return result

    def create_tasks(self, tasks):
        """
        tasks: array = {[
            "project_id": 123454325,
            "task": "Doing work",
        }]
        """
        result = []
        for task in tasks:
            result.append(self.create_task(task))
        return result

    def create_task(self, task):
        """
        task: dict = {
            "project_id": 123454325,
            "task": "Doing work",
        }
        """
        pid = task["project_id"]
        task = task["task"]
        url = f"{self.url}/projects/{pid}/tasks"
        payload = {"name": task, "status": "ACTIVE"}
        response = requests.post(url, json=payload, headers=self.headers)

        if response.status_code == 201:
            msg = f'201 - Task "{task} #{id}" created.'
            logging.info(msg)
            return {**response.json(), **{"error": False, "error_message": msg}}
        else:
            msg = f'{response.status_code} - Error: "{response.text}"'
            logging.error(msg)
            return {"error": True, "message": msg}

    def archive_projects(self, project_ids: list = []):
        result = []
        for id in project_ids:
            url = f"{self.url}/projects/{id}"
            payload = {"archived": True}
            response = requests.put(url, json=payload, headers=self.headers)
            if response.status_code == 200:
                msg = f"200 - Project #{id} archived"
                logging.info(msg)
                result.append({"error": False, "error_message": msg})
            else:
                msg = f"{response.status_code} - Error: '{response.text}'"
                logging.info(msg)
                result.append({"error": True, "error_message": msg})
        return result

    def delete_projects(self, project_ids: list = []):
        result = []
        for id in project_ids:
            url = f"{self.url}/projects/{id}"
            response = requests.delete(url, headers=self.headers)
            if response.status_code == 200:
                msg = f"200 - Project #{id} deleted"
                logging.info(msg)
                result.append({"error": False, "message": msg})
            else:
                msg = f'{response.status_code} - Error: "{response.text}"'
                logging.error(msg)
                result.append({"error": True, "message": msg})
        return result

    def get_time_entries(self, start, end, query={}):
        start = f"{start.isoformat()}T00:00:00Z"
        end = f"{end.isoformat()}T00:00:00Z"
        url = f"{self.url}/user/{self.user}/time-entries"
        query = {
            **{"start": f"{start}", "end": f"{end}", "hydrated": "true"},
            **query,
        }
        response = requests.get(url, params=query, headers=self.headers)

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


def odoo_id_from_note(note):
    match = re.search(r"odoo_id=(\d+)$", note)
    if match:
        return int(match[1])


def odoo_id_from_task(task):
    match = re.search(r"#(\d+)$", task)
    if match:
        return int(match[1])


def calculate_duration(start, end):

    s = datetime.fromisoformat(start[:-1])
    e = datetime.fromisoformat(end[:-1])
    return (e - s).total_seconds()


def date_to_timestamp(date: date):
    return f"{date.isoformat()}T00:00:00Z"
