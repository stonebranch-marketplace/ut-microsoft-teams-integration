################################################################################
#    Name: handler.py
#    Purpose: Microsoft Teams integration with UAC
#    Origins: Stonebranch GmbH
#    Author:  Karthik Mohan
#    Prerequisites:
#     - Universal Agent for Windows/Linux
#     - Python 3.6.x
#     - Requires the Python modules to be installed
#     - pip install requests
#
#    Version History:
#    1.0     KM        Initial Version
#
#    Copyright (c) Stonebranch GmbH, 2019.  All rights reserved.
#
#    The copyright in this work is vested in Stonebranch.
#    The information contained in this work (either in whole or in part)
#    is confidential and must not be modified, reproduced, disclosed or
#    disseminated to others or used for purposes other than that for which
#    it is supplied, without the prior written permission of Stonebranch.
#    If this work or any part hereof is furnished to a third party by
#    virtue of a contract with that party, use of this work by such party
#    shall be governed by the express contractual terms between Stonebranch,
#    which is party to that contract and the said party.
#
#    The information in this document is subject to change without notice
#    and should not be construed as a commitment by Stonebranch.
#    Stonebranch assumes no responsibility for any errors that may appear in
#    this document.
#
#    With the appearance of a new version of this document all older versions
#    become invalid.
################################################################################


import json
import boto3
import logging
from urllib.parse import parse_qs
import requests

version = "1.0"

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    print(str(event))
    logger.info(json.dumps(event))
    payload = event['body']
    print(payload)
    jobname_split = payload.split(':')
    jobname = jobname_split[1]
    team_button = jobname_split[0]
    print(team_button)
    print(jobname)
    ###################### Teams Channel Data ################
    teams_incoming_webhook = 'https://outlook.office.com/webhook/dbc988a0' \
                             '-69eb-45b9-b70a-569906b07c23@74d8ca68-991f-47c9' \
                             '-bb24-f85b441cc605/IncomingWebhook/b9c6df76d67e443085ee29afdcee3b8b/f777a5f6-c742-4203-8a50-05f33330ca91'
    ###################### End of Teams Channel Data ################
    ###################### Credentials for universal controller ################
    uname = 'chatops'
    passwd = 'canton123'
    uc_url = 'http://' + uname + ':' + passwd + \
             '@frankfurt.stonebranchdev.cloud:8080/opswise/resources' \
             '/taskinstance/setcompleted'
    ###################################### End of Universal Controller
    # Credentials ###############################
    # Posting request to Universal Controller
    uc_post_request(team_button, jobname, uc_url, teams_incoming_webhook)
    #################################Teams data parsed -completed
    # ###########################
    body = {
        "message": "Teams Data parsed successfully and Universal controller "
                   "confirmed the job !",
        "input": event
    }
    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }
    return response


def uc_post_request(team_button, jobname, uc_url, teams_incoming_webhook):
    header = {'content-type': "application/json"}
    if team_button=="Approved":
        print("Intiating Request to Universal Controller")
        approval_message = {
            "name": jobname,
            "criteria": "Newest Instance"
        }
        print(uc_url)
        try:
            post_uc = requests.post(uc_url, data=json.dumps(approval_message),
                headers=header)
            if post_uc.status_code==200:
                format_response = post_uc.json()
                logger.info(format_response)
                if format_response['success'] is False:
                    print("Something went wrong")
                    error_message = {
                        '@type': "MessageCard",
                        '@context': "https://schema.org/extensions",
                        'summary': "This is the summary property",
                        'themeColor': "#FFFF00",
                        'sections': [
                            {
                                "activityTitle":"**Couldn't not reach**",
                                "activitySubtitle":"Something went wrong, "
                                                 "action not completed"
                            }
                        ]
                    }
                    print("Sending error report to MS Teams Channel")
                    try:
                        uc_response = requests.post(teams_incoming_webhook,
                            data=json.dumps(error_message),
                            headers={'CARD-UPDATE-IN-BODY': 'True',
                                     'Content-Type': 'application/json'})
                    except Exception as e:
                        logger.error(e)
                elif format_response['success'] is True:
                    print("Your request is approved")
                    approval_response = {
                        "@type": "MessageCard",
                        "@context": "https://schema.org/extensions",
                        "summary": "This is the summary property",
                        "themeColor": "#008000",
                        "sections": [
                            {
                                "activityTitle": "**Approved**",
                                "activitySubtitle": "Request was approved "
                                                    "after "
                                                    "review"
                            }
                        ]
                    }
                    header = {
                        'content-type': 'application/json'
                    }
                    print("Sending Notification to MS Teams Channel")
                    try:
                        uc_response = requests.post(teams_incoming_webhook,
                            data=json.dumps(approval_response), headers=header)
                        format_response = json.loads(uc_response.text)
                        print(format_response)
                    except Exception as e:
                        logger.error(e)
        except Exception as e:
            logger.error(e)
    elif team_button=="Rejected":
        print("Reqeust Denied")
        reject_response = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": "This is the summary property",
            "themeColor": "#FF0000",
            "sections": [
                {
                    "activityTitle": "**Rejected**",
                    "activitySubtitle": "Request was rejected after review"
                },
            ]
        }
        print("Sending Notification to MS Teams Channel")
        try:
            uc_response = requests.post(teams_incoming_webhook,
                data=json.dumps(reject_response),
                headers={'CARD-UPDATE-IN-BODY': 'True',
                         'Content-Type': 'application/json'})
            print("Teams Response: ", uc_response.status_code)
        except Exception as e:
            logger.error(e)
