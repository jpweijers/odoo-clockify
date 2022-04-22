import logging

# remove root logging handler so that logging works with cloudwatch
logging.root.handlers = []
logging.basicConfig(level=logging.INFO)


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
