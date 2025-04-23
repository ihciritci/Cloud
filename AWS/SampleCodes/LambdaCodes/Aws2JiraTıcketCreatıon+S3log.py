import json
import os
import base64
import urllib.request
import urllib.error
import boto3
from datetime import datetime

s3 = boto3.client('s3')

def lambda_handler(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])

    alarm_name = message.get('AlarmName', 'Unknown Alarm')
    state = message.get('NewStateValue', 'Unknown')
    reason = message.get('NewStateReason', 'No reason provided.')

    if state == "ALARM":
        jira_url = "https://inlinedata.atlassian.net/rest/api/3/issue"
        email = os.environ['JIRA_EMAIL']
        api_token = os.environ['JIRA_API_TOKEN']
        auth = base64.b64encode(f"{email}:{api_token}".encode()).decode()

        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json"
        }

        summary_text = f"Alarm Triggered: {alarm_name}"

        data = {
            "fields": {
                "project": { "key": "ICRM" },
                "summary": summary_text,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": reason
                                }
                            ]
                        }
                    ]
                },
                "issuetype": { "name": "Task" }
            }
        }

        json_data = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(jira_url, data=json_data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req) as response:
                result = response.read().decode()
                print("Response:", result)

                
                write_log_to_s3(summary_text, reason, result)

        except urllib.error.HTTPError as e:
            error_details = e.read().decode()
            print("HTTPError:", e.code, error_details)
        except Exception as e:
            print("Error:", str(e))


def write_log_to_s3(summary, reason, jira_response):
    bucket_name = os.environ['S3_BUCKET_NAME']     
    log_key = f"jira_logs/{datetime.utcnow().strftime('%Y-%m-%d')}.log"

    log_entry = f"""
----------------------------------------
Time: {datetime.utcnow().isoformat()} UTC
Summary: {summary}
Reason: {reason}
Jira Response: {jira_response}
----------------------------------------
"""

    try:
        # Var olan log dosyasını al
        existing_log = ""
        try:
            obj = s3.get_object(Bucket=bucket_name, Key=log_key)
            existing_log = obj['Body'].read().decode('utf-8')
        except s3.exceptions.NoSuchKey:
            pass  # Dosya yoksa, sorun değil.

        updated_log = existing_log + log_entry
        s3.put_object(Bucket=bucket_name, Key=log_key, Body=updated_log.encode('utf-8'))
        print(f"Log written to {bucket_name}/{log_key}")
    except Exception as e:
        print("Failed to write to S3:", str(e)) 
