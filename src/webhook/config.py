import os

ODOO_URL = os.environ["ODOO_URL"]
ODOO_LOGIN = os.environ["ODOO_LOGIN"]
ODOO_PASSWORD = os.environ["ODOO_PASSWORD"]

CLOCKIFY_URL = os.environ["CLOCKIFY_URL"]
CLOCKIFY_KEY = os.environ["CLOCKIFY_KEY"]
CLOCKIFY_WORKSPACE = os.environ["CLOCKIFY_WORKSPACE"]
CLOCKIFY_CLIENT_ID = os.environ["CLOCKIFY_CLIENT_ID"]
CLOCKIFY_USER = os.environ["CLOCKIFY_USER"]

CLOCKIFY_WEBHOOK_SIGNATURE_UPDATED = os.environ["CLOCKIFY_WEBHOOK_SIGNATURE_UPDATED"]
CLOCKIFY_WEBHOOK_SIGNATURE_STOPPED = os.environ["CLOCKIFY_WEBHOOK_SIGNATURE_STOPPED"]
CLOCKIFY_WEBHOOK_SIGNATURE_DELETED = os.environ["CLOCKIFY_WEBHOOK_SIGNATURE_DELETED"]
CLOCKIFY_WEBHOOK_SIGNATURE_MANUAL = os.environ["CLOCKIFY_WEBHOOK_SIGNATURE_MANUAL"]

TABLE_NAME = os.environ.get("DYNAMODB_TABLE")
