import json


def lambda_handler(event, context):
    # API Gateway wraps body as a JSON string; direct invoke passes dict directly
    if "body" in event:
        body = json.loads(event["body"] or "{}")
    else:
        body = event

    name = body.get("name", "world")

    return {
        "statusCode": 200,
        "body": json.dumps({"message": f"Hello, {name}!"})
    }
