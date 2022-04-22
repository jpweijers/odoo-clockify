import os

from request_processor import process_request


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
