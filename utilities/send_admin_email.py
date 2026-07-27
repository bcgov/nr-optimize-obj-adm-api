import os
import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from . import constants

def send_admin_email(message_detail):

    msg = MIMEMultipart("related")
    msg["Subject"] = "nr-optimize-obj-adm-api Script Report"
    msg["To"] = constants.DEBUG_EMAIL
    msg["From"] = constants.FROM_EMAIL

    dir_path = os.path.dirname(os.path.realpath(__file__))
    host_name = socket.gethostname()
    html = (
        "<html><head></head><body><p>"
        + "nr-optimize-obj-adm-api has sent an automated report email."
        + "<br />Server: "
        + str(host_name)
        + "<br />File Path: "
        + dir_path
        + "<br />"
        + str(message_detail)
        + "</p></body></html>"
    )
    msg.attach(MIMEText(html, "html"))
    s = smtplib.SMTP(constants.SMTP_SERVER)
    s.sendmail(msg["From"], msg["To"], msg.as_string())
    s.quit()