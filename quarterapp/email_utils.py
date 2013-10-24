#
#  Copyright (c) 2013 Markus Eliasson, http://www.quarterapp.com/
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import smtplib
import logging
import sys

import tornado.template
from tornado.options import options

signup_email_template = tornado.template.Template("""From: Quarterapp <{{ email_from }}>
To: {{ email_to }}
Subject: {{ subject }}

Welcome to Quarterapp in order to complete your free registration you need to activate
your account.

Follow this link to complete the activation: {{ code_link }}

If the above link does not work, go to {{ link }} and enter the code manually.

Activation code: {{ code }}

Cheers!
 Quarterapp team

""")

reset_email_template = tornado.template.Template("""From: Quarterapp <{{ email_from }}>
To: {{ email_to }}
Subject: {{ subject }}

Someone - hopefully you - reported that you forgot your password to Quarterapp.

Follow this link to assign a new password to your account: {{ code_link }}

If the above link does not work, go to {{ link }} and enter the code manually.

Reset code: {{ code }}

If you did not ask to reset your password, please ignore this mail.

Cheers!
 Quarterapp team

""")


def send_mail(username, message):
    try:
        server = smtplib.SMTP(options.mail_host)

        if len(options.mail_user) > 0:
            logging.info("Using email authentication ")
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(options.mail_user, options.mail_password)
            
        server.sendmail(options.mail_sender, username, message)
        return True
    except Exception, e:
        logging.warn("Could not send email")
        logging.exception(e)
        logging.warn(message)
        return True


def send_signup_email(username, code):
    """
    Sends the activation email to the given address with the given activation code.

    @param username The username to send the email to
    @param code The activation code
    @return True if mail could be sent, else False
    """
    try:
        message = signup_email_template.generate(subject="Welcome to quarterapp",
                                                 email_from=options.mail_sender,
                                                 email_to=username,
                                                 code_link="http://" + options.base_url + "/activate/" + code,
                                                 link="http://" + options.base_url + "/activate",
                                                 code=code)
        return send_mail(username, message)
    except Exception, e:
        logging.warn("Could not send signup email")
        logging.exception(e)
        return False


def send_reset_email(username, code):
    """
    Sends the password reset email to the given address with the given reset code.
    @param username The username to send the email to
    @param code The activation code
    @return True if mail could be sent, else False
    """
    try:
        message = reset_email_template.generate(subject="Reset your password",
                                                email_from=options.mail_sender,
                                                email_to=username,
                                                code_link="http://" + options.base_url + "/reset/" + code,
                                                link="http://" + options.base_url + "/reset",
                                                code=code)
        return send_mail(username, message)
    except Exception, e:
        logging.error("Could not send reset email!")
        logging.exception(e)
        return False
