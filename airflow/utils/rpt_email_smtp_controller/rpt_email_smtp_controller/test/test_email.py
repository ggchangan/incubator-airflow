from test._mock_backport import MagicMock

from rpt_email_smtp_controller.rpt_email_smtp_controller import RPTCustomEmailAlerter
from rpt_email_smtp_controller.rpt_email_smtp_controller import send_email_smtp_controller

import unittest


class RPTCustomEmailAlerterTest(unittest.TestCase):

    def setUp(self):

        self.subject_original_str = "Airflow alert: <TaskInstance: email-retry-2.templated 2017-12-06 00:00:00 [up_for_retry]>"
        self.body_original_str = """
            Try 1 out of 3<br>
            Exception:<br>Exception
            Bash command failed<br>
            Log: <a href='Link'>Link</a><br>
            Host: PRD-002<br>
            Log file: /Users/renzhang/airflow/logs/email-alert-2/templated/2017-12-04T00:00:00.log<br>
            Mark success: <a href='Link'>Link</a><br>
        """


    def test_get_subject(self):
        rpt_custom_email_alerter = RPTCustomEmailAlerter()
        get_email_env_mock = MagicMock()
        get_email_env_mock.return_value = "PRD.AWS"
        rpt_custom_email_alerter._RPTCustomEmailAlerter__get_email_env = get_email_env_mock
        subject_str = rpt_custom_email_alerter.get_subject(self.subject_original_str, self.body_original_str)
        expect_str = "[WARN][PRD][ANALYTICS][PRD-002][AWS] Airflow alert: <TaskInstance: email-retry-2.templated 2017-12-06 00:00:00 [up_for_retry]>"
        self.assertEquals(expect_str, subject_str)


    def test_sure_called_by_me(self):
        rpt_custom_email_alerter = RPTCustomEmailAlerter()
        self.assertTrue(rpt_custom_email_alerter.sure_called_by_me(self.subject_original_str, self.body_original_str))

    def test_send_email(self):
        rpt_custom_email_alerter = RPTCustomEmailAlerter()
        to = "renzhang@freewheel.tv"
        rpt_custom_email_alerter.send_email(to, self.subject_original_str, self.body_original_str)

    def test_send_email_smtp_controller(self):
        to = "renzhang@freewheel.tv"
        # default sender
        subject = "test for default sender"
        send_email_smtp_controller(to, subject, self.body_original_str)

        #custom sender
        send_email_smtp_controller(to, self.subject_original_str, self.body_original_str)



if __name__ == '__main__':
    unittest.main()
