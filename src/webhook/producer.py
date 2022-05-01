import json
import logging
import os

import boto3

from config import *

QUEUE_URL = os.environ.get("QUEUE_URL")
SQS = boto3.client("sqs")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def updated(event: dict = {}, context: dict = {}) -> dict:
    return queue_message(event, CLOCKIFY_WEBHOOK_SIGNATURE_UPDATED)


def stopped(event={}, contxt={}):
    return queue_message(event, CLOCKIFY_WEBHOOK_SIGNATURE_STOPPED)


def deleted(event={}, contxt={}):
    return queue_message(event, CLOCKIFY_WEBHOOK_SIGNATURE_DELETED)


def manual(event={}, contxt={}):
    return queue_message(event, CLOCKIFY_WEBHOOK_SIGNATURE_MANUAL)


def queue_message(event: dict, secret: str) -> dict:
    logger.info(f"Event: {json.dumps(event)}")
    if request_is_signed(event, secret):
        status_code = 200
        message = ""

        try:
            message_attrs = {
                "AttributeName": {"StringValue": "AttributeValue", "DataType": "String"}
            }
            SQS.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=event["body"],
                MessageAttributes=message_attrs,
            )
            message = "Request accepted"

        except Exception as e:
            logger.exception("Sending message to SQS failed")
            message = "Internal server error"
            status_code = 500

        return {"statusCode": status_code, "body": json.dumps({"message": message})}

    return {"statusCode": 401, "body": "Unauthorized"}


def request_is_signed(event, signature) -> bool:
    if all(k in event for k in ["body", "headers"]):
        signed = signature == event["headers"].get("clockify-signature")
        if signed:
            return True
    return False
