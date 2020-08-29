import boto3
import datetime
from dateutil.parser import parse
import json
import os
from urllib import request

CM_URL = "https://citymapper.com/api/1/gettrip?slug={}"
CW_UPDATE_EVENT = os.environ.get("CW_UPDATE_EVENT")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
ETA_KEY = os.environ.get("ETA_KEY")
SLUG_KEY = os.environ.get("SLUG_KEY")

s3 = boto3.resource("s3")
events = boto3.client("events")


def get_eta_minutes(slug):
    try:
        with request.urlopen(CM_URL.format(slug)) as response:
            doc = json.loads(response.read())
    except:
        return -1
    now = datetime.datetime.utcnow()
    now = now.replace(tzinfo=datetime.timezone.utc)
    if doc["status"] in {"arrived", "expired"}:
        return -1
    eta = parse(doc["eta"])
    minutes = (eta - now).total_seconds() / 60
    return min(minutes, 45)


def update_angle(minutes):
    if minutes == -1:
        angle = 0
    else:
        angle = int(minutes * 2048 / 45)

    eta_object = s3.Object(BUCKET_NAME, ETA_KEY)
    eta_object_acl = s3.ObjectAcl(BUCKET_NAME, ETA_KEY)

    eta_object.put(Body=f"{angle}".encode("utf-8"))
    eta_object_acl.put(ACL="public-read")


def lambda_handler(event, context):
    slug_object = s3.Object(BUCKET_NAME, SLUG_KEY)

    if event.get("queryStringParameters"):
        # This is a request via API Gateway, save the new slug
        slug = event["queryStringParameters"]["content"].split("/")[-1]
        slug_object.put(Body=slug.encode("utf-8"))

        # enable the update timer
        events.enable_rule(Name=CW_UPDATE_EVENT)
    else:
        # This is an update triggered by Cloudwatch events
        slug = slug_object.get()["Body"].read().decode("utf-8")

    minutes = get_eta_minutes(slug)

    if minutes == -1:
        # cancel the update timer
        events.disable_rule(Name=CW_UPDATE_EVENT)

    update_angle(minutes)

    return {
        "statusCode": 200,
        # Displayed as toast after successful share:
        "body": json.dumps("ETA successfully sent to clock!")
    }
