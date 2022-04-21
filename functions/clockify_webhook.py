import logging
import json
import os
from datetime import date, timedelta

import clockify.clockify as clockify

CLOCKIFY_URL = os.environ["CLOCKIFY_URL"]
CLOCKIFY_KEY = os.environ["CLOCKIFY_KEY"]
CLOCKIFY_WORKSPACE = os.environ["CLOCKIFY_WORKSPACE"]
CLOCKIFY_CLIENT_ID = os.environ["CLOCKIFY_CLIENT_ID"]
CLOCKIFY_USER = os.environ["CLOCKIFY_USER"]
CLOCKIFY_WEBHOOK_SIGNATURE = os.environ["CLOCKIFY_WEBHOOK_SIGNATURE"]

# remove root logging handler so that logging works with cloudwatch
logging.root.handlers = []
logging.basicConfig(level=logging.INFO)


def handler(event={}, context={}):
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
                start = f"{start.isoformat()}T00:00:00Z"
                end = f"{end.isoformat()}T00:00:00Z"

                print(start, end)
                return {"Accepted": True}
        return {"Accepted": False}

    logging.info(f"Event: {event}")
    logging.info(f"Context: {context}")
    return {"Test": True}


test_event = {
    "version": "2.0",
    "routeKey": "POST /clockify/webhook",
    "rawPath": "/clockify/webhook",
    "rawQueryString": "",
    "headers": {
        "clockify-signature": "YC6Je9nBl50faeycgNIAqlztlAwpGAAi",
        "clockify-webhook-event-type": "TIMER_STOPPED",
        "content-length": "1317",
        "content-type": "application/json",
        "host": "15oyrc2l50.execute-api.eu-west-1.amazonaws.com",
        "user-agent": "Vert.x-WebClient/4.2.5",
        "x-amzn-trace-id": "Root=1-6260ff02-56d68a3111923ad94e73cc9f",
        "x-forwarded-for": "18.157.52.94",
        "x-forwarded-port": "443",
        "x-forwarded-proto": "https",
    },
    "requestContext": {
        "accountId": "297888190818",
        "apiId": "15oyrc2l50",
        "domainName": "15oyrc2l50.execute-api.eu-west-1.amazonaws.com",
        "domainPrefix": "15oyrc2l50",
        "http": {
            "method": "POST",
            "path": "/clockify/webhook",
            "protocol": "HTTP/1.1",
            "sourceIp": "18.157.52.94",
            "userAgent": "Vert.x-WebClient/4.2.5",
        },
        "requestId": "Q6zIZikSDoEEMaA=",
        "routeKey": "POST /clockify/webhook",
        "stage": "$default",
        "time": "21/Apr/2022:06:51:46 +0000",
        "timeEpoch": 1650523906371,
    },
    "body": '{"id":"6260fee78065a229df4561dd","description":"cloud practitioner","userId":"625cf4a6a7d9d34012f70de1","billable":true,"projectId":"625d15dfbea8f62f6f3aa377","timeInterval":{"start":"2022-04-21T06:51:17Z","end":"2022-04-21T06:51:43Z","duration":"PT26S"},"workspaceId":"625cf4a6a7d9d34012f70de2","isLocked":false,"hourlyRate":null,"costRate":null,"customFieldValues":[],"currentlyRunning":false,"project":{"name":"Kabisa - Persoonlijke Ontwikkeling","clientId":"625cf508a59c3f5bb60a2b25","workspaceId":"625cf4a6a7d9d34012f70de2","billable":true,"estimate":{"estimate":"PT0S","type":"AUTO"},"color":"#009688","archived":false,"clientName":"Kabisa","duration":"PT4H59M1S","note":"odoo_id=857","activeEstimate":"NONE","timeEstimate":{"includeNonBillable":true,"estimate":0,"type":"AUTO","resetOption":null},"budgetEstimate":null,"id":"625d15dfbea8f62f6f3aa377","public":false,"template":false},"task":{"name":"Research / Zelfstudie #8494","projectId":"625d15dfbea8f62f6f3aa377","assigneeId":"","assigneeIds":[],"userGroupIds":[],"estimate":"PT0S","status":"ACTIVE","workspaceId":"625cf4a6a7d9d34012f70de2","budgetEstimate":0,"billable":true,"hourlyRate":null,"costRate":null,"id":"625d15df75a4b64878ccc690","duration":"PT2H59M1S"},"user":{"id":"625cf4a6a7d9d34012f70de1","name":"JP Weijers","status":"ACTIVE"},"tags":[]}',
    "isBase64Encoded": False,
}
if __name__ == "__main__":
    result = handler(test_event, {})
    print(result)
