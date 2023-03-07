from config import smtp_port,smtp_email,smtp_password,smtp_server,pushover_token,slack_webhook
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json
import urllib.parse
from app import make_celery
from blueprints.deployement.models import deployments
from blueprints.admin.models import admin_notification_settings
celery = make_celery()
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



@celery.task
def send_notifications(deploy_id,process_finished):
    dep = deployments.query.filter_by(deploy_id=deploy_id).first()
    n = admin_notification_settings.query.filter_by().first()
    if n.slack and dep.notifications["slack"] :
        if process_finished=="refetched":
            slackmessage = "New changes(commit : %s) for %s fetched"%(dep.commit_hash[:7],dep.primary_domain)
        else:
            slackmessage = "%s has been %s to commit %s"%(dep.primary_domain,process_finished,dep.commit_hash[:7])
        send_slack_notification(slack_webhook,slackmessage)
    
    if process_finished=="refetched":
        subj = "New changes(commit : %s) for %s fetched"%(dep.commit_hash[:7],dep.primary_domain)
        email_body = {}
        email_body["text"]="New changes(commit : %s) for %s fetched"%(dep.commit_hash[:7],dep.primary_domain)
        email_body["html"]="""/
        <html>
       <body>
       <p>"New changes(commit :<a href="https://github.com/%s/%s/commit/%s"> %s<a>) for <a href="https://%s">%s</a> fetched
       </body>
        </html>
        """%(dep.repo_owner,dep.repo_name,dep.commit_hash,dep.commit_hash[:7],dep.primary_domain,dep.primary_domain)
    else:
        subj = "%s has been %s to commit %s"%(dep.primary_domain,process_finished,dep.commit_hash[:7])
        email_body = {}
        email_body["text"]="%s has been %s to commit %s"%(dep.primary_domain,process_finished,dep.commit_hash[:7])
        email_body["html"]="""
        <html>
        <body>
    <p>   "<a href="https://%s">%s</a> has been %s to commit <a href="https://github.com/%s/%s/commit/%s">%s</a>            </p>
        </body>
        </html>
        """%(dep.primary_domain,dep.primary_domain,process_finished,dep.repo_owner,dep.repo_name,dep.commit_hash,dep.commit_hash[:7])
    if n.email:
        for email in dep.notifications["email"]:
            try:
                send_email(email,subj,email_body)
            except:
                continue
    if process_finished=="refetched":
        pushover_title = "New changes for %s fetched"%(dep.primary_domain)
        pushover_message = "New changes(commit : %s) for %s fetched"%(dep.commit_hash[:7],dep.primary_domain)
    else:
        pushover_title = "%s %s"%(dep.primary_domain,process_finished)
        pushover_message = "%s has been %s to commit %s"%(dep.primary_domain,process_finished,dep.commit_hash[:7])
    if n.pushover:
        for userkey in dep.notifications["pushover"]:
            try:
                send_pushover_notification(userkey,pushover_title,pushover_message)
            except:
                continue
    
