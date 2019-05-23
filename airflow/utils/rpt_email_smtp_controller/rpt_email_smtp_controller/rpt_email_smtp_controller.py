import re
from abc import abstractmethod

from airflow.utils.email import send_email_smtp
from airflow import configuration
from airflow.utils.log.logging_mixin import LoggingMixin


def send_email_smtp_controller(to, subject, html_content, files=None, dryrun=False, cc=None, bcc=None,
                               mime_subtype='mixed', mime_charset='us-ascii'):
    log = LoggingMixin().logger

    custom_alerts = get_custom_alerters()
    for custom_alert in custom_alerts:
        if custom_alert.sure_called_by_me(subject, html_content):
            log.info("Sent an alert email by custom %s", custom_alert.__class__)

            try:
                custom_alert.send_email(to, subject, html_content, files, dryrun, cc, bcc, mime_subtype)
            except Exception, e:
                log.warning("Custom alert email subject except %s", e.message)
                break

            return

    log.info("Sent an alert email by default %s", "send_email_smtp")
    send_email_smtp(to, subject, html_content, files, dryrun, cc, bcc, mime_subtype, mime_charset)


"""
the factory method for all alerters
"""


def get_custom_alerters():
    custom_alerters = [RPTCustomEmailAlerter()]
    return custom_alerters


"""
Base class for all Alerters
"""


class CustomEmailAlerter:
    def __init__(self):
        pass

    @abstractmethod
    def sure_called_by_me(self, subject, html_content): pass

    @abstractmethod
    def send_email(self, to, subject, html_content, files=None, dryrun=False, cc=None, bcc=None,
                   mime_subtype='mixed'): pass


class RPTCustomEmailAlerter(CustomEmailAlerter):
    def __init__(self):
        self.email_state = ""
        self.email_env = ""
        self.email_location = ""
        self.hostname = ""
        self.task = ""

    def sure_called_by_me(self, subject, html_content):
        alert_found = subject.find("alert") != -1
        try_found = html_content.find("Try") != -1
        exception_found = html_content.find("Exception") != -1
        log_found = html_content.find("Log") != -1
        host_found = html_content.find("Host") != -1
        log_file_found = html_content.find("Log file") != -1
        mark_success_found = html_content.find("Mark success") != -1
        return alert_found and try_found and exception_found and \
               log_found and host_found and log_file_found and mark_success_found

    def send_email(self, to, subject, html_content, files=None, dryrun=False, cc=None, bcc=None, mime_subtype='mixed'):
        subject = self.get_subject(subject, html_content)
        send_email_smtp(to, subject, html_content, files, dryrun, cc, bcc, mime_subtype)

    def get_subject(self, subject, html_content):
        lines = html_content.split("<br>")
        if len(lines) != 8:
            raise Exception("Invalid alert body!")

        try_line = lines[0]
        try_number_strs = re.findall(r"\d+\.?\d*", try_line)
        if len(try_number_strs) != 2:
            raise Exception("The first line of alert email body is invalid!")

        try_number = int(try_number_strs[0])
        max_tries = int(try_number_strs[1])

        self.task = subject[subject.find(':') + 1:]
        hostname_line = lines[4]
        self.hostname = hostname_line[hostname_line.find(':') + 2:]
        self.email_state = try_number >= max_tries and "FAIL" or "WARN"

        self.email_env = self.__get_email_env()

        env_location_dict = {
            'PRD.AWS': 'AWS', "STG.AWS": "AWS", "DEV.AWS" : "AWS",
            'PRD': 'NYC', 'STG': 'NYC', 'DEV': 'PEK', 'UNKNOWN': 'UNKNOWN'
        }

        self.email_location = env_location_dict.get(self.email_env, "AWS")

        return self.__format_subject()

    def __get_email_env(self):
        return configuration.get('email', 'EMAIL_ENV').upper()

    def __format_subject(self):
        email_env = self.email_env.split(".")[0]
        return "[{self.email_state}][{email_env}][ANALYTICS][{self.hostname}][{self.email_location}] Airflow " \
               "alert:{self.task}".format(**locals())
