from config import smtp_port,smtp_email,smtp_password,smtp_server,pushover_token
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json
import urllib.parse

def send_email(to_address,email_subject,email_body):
    
    message = MIMEMultipart("alternative")
    message["Subject"] = email_subject
    message["From"] = smtp_email
    message["To"] = to_address
    context = ssl.create_default_context()
    part1 = MIMEText(email_body["text"], "plain")
    part2 = MIMEText(email_body["html"], "html")
    message.attach(part1)
    message.attach(part2)
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
        server.login(smtp_email, smtp_password)
        server.sendmail(smtp_email, to_address, message.as_string())
        

def send_slack_notification(webhook_url,message):
    payload = {
    "text": message
     }
    requests.post(webhook_url, data=json.dumps(payload), headers={"Content-Type": "application/json"})


def send_pushover_notification(user_key,title,message):
    
    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": pushover_token,
        "user": user_key,
        "message": message,
        "title":title
    }
    headers = {"Content-type": "application/x-www-form-urlencoded"}
    encoded_data = urllib.parse.urlencode(data).encode("utf-8")
    response = requests.post(url, data=encoded_data, headers=headers)


