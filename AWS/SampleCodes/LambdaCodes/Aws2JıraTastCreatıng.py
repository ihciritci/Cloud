import json
import os
import base64
import urllib.request
import urllib.error

def lambda_handler(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])

    alarm_name = message['AlarmName']
    state = message['NewStateValue']
    reason = message['NewStateReason']

    if state == "ALARM":
        jira_url = "https://inlinedata.atlassian.net/rest/api/3/issue"

        email = os.environ['JIRA_EMAIL']
        api_token = os.environ['JIRA_API_TOKEN']
        auth = base64.b64encode(f"{email}:{api_token}".encode()).decode()

        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json"
        }

        data = {"fields": {
        "project": { "key": "ICRM" },  # Project key doğru olacak
        "summary": f"Alarm Triggered: {"Test1612"}",
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
        except urllib.error.HTTPError as e:
            error_details = e.read().decode()
            print("HTTPError:", e.code, error_details)
        except Exception as e:
            print("Error:", str(e))
