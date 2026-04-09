from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

import boto3
from botocore.exceptions import ClientError

DDB = boto3.client("dynamodb")
SNS = boto3.client("sns")  # opcional

BATCHES_TABLE = os.getenv("BATCHES_TABLE", "batches")
BATCH_ITEMS_TABLE = os.getenv("BATCH_ITEMS_TABLE", "batch_items")
BATCH_COMPLETED_TOPIC_ARN = os.getenv("BATCH_COMPLETED_TOPIC_ARN", "")  # opcional


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ttl_days(days: int) -> int:
    return int(time.time()) + days * 24 * 3600


def create_batch(batch_id: str, expected: int) -> None:
    DDB.put_item(
        TableName=BATCHES_TABLE,
        Item={
            "batch_id": {"S": batch_id},
            "expected": {"N": str(expected)},
            "done": {"N": "0"},
            "failed": {"N": "0"},
            "status": {"S": "RUNNING"},
            "created_at": {"S": utc_iso()},
        },
        ConditionExpression="attribute_not_exists(batch_id)",
    )


def try_register_item_once(
    batch_id: str,
    item_id: str,
    state: str,
    ttl: Optional[int] = None,
) -> bool:
    """
    Garante idempotência: só a primeira vez conta.
    Retorna True se inseriu (primeira vez), False se já existia (duplicata).
    """
    item = {
        "batch_id": {"S": batch_id},
        "item_id": {"S": item_id},
        "state": {"S": state},
        "updated_at": {"S": utc_iso()},
    }
    if ttl is not None:
        item["ttl"] = {"N": str(ttl)}

    try:
        DDB.put_item(
            TableName=BATCH_ITEMS_TABLE,
            Item=item,
            ConditionExpression="attribute_not_exists(batch_id) AND attribute_not_exists(item_id)",
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


def increment_batch_counters(batch_id: str, done_inc: int = 0, failed_inc: int = 0) -> Tuple[int, int, int]:
    """
    Incrementa done/failed do batch e retorna (expected, done, failed) após o update.
    """
    update_parts = []
    ean: Dict[str, str] = {"#status": "status", "#expected": "expected", "#done": "done", "#failed": "failed"}
    eav: Dict[str, Dict[str, str]] = {":running": {"S": "RUNNING"}}

    if done_inc:
        update_parts.append("ADD #done :d")
        eav[":d"] = {"N": str(done_inc)}

    if failed_inc:
        update_parts.append("ADD #failed :f")
        eav[":f"] = {"N": str(failed_inc)}

    if not update_parts:
        # não deve ocorrer no uso normal
        update_parts.append("SET _noop = :noop")
        eav[":noop"] = {"S": "noop"}

    resp = DDB.update_item(
        TableName=BATCHES_TABLE,
        Key={"batch_id": {"S": batch_id}},
        UpdateExpression=" ".join(update_parts),
        ExpressionAttributeNames=ean,
        ExpressionAttributeValues=eav,
        ConditionExpression="attribute_exists(batch_id) AND #status = :running",
        ReturnValues="ALL_NEW",
    )

    attrs = resp["Attributes"]
    expected = int(attrs["expected"]["N"])
    done = int(attrs["done"]["N"])
    failed = int(attrs["failed"]["N"])
    return expected, done, failed


def try_close_batch_if_all_finished(batch_id: str) -> bool:
    """
    Fecha o batch quando done + failed == expected.
    Só um worker vai conseguir devido ao ConditionExpression.
    """
    try:
        DDB.update_item(
            TableName=BATCHES_TABLE,
            Key={"batch_id": {"S": batch_id}},
            UpdateExpression="SET #status = :completed, completed_at = :ts",
            ExpressionAttributeNames={
                "#status": "status",
                "#expected": "expected",
                "#done": "done",
                "#failed": "failed",
            },
            ExpressionAttributeValues={
                ":running": {"S": "RUNNING"},
                ":completed": {"S": "COMPLETED"},
                ":ts": {"S": utc_iso()},
            },
            # condição: ainda está RUNNING e (done + failed) == expected
            ConditionExpression="#status = :running AND (#done + #failed) = #expected",
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


def publish_batch_completed(batch_id: str, expected: int, done: int, failed: int) -> None:
    if not BATCH_COMPLETED_TOPIC_ARN:
        return

    SNS.publish(
        TopicArn=BATCH_COMPLETED_TOPIC_ARN,
        Message=json.dumps(
            {
                "event_type": "BATCH_COMPLETED",
                "batch_id": batch_id,
                "expected": expected,
                "done": done,
                "failed": failed,
                "ts": utc_iso(),
            }
        ),
        MessageAttributes={
            "event_type": {"DataType": "String", "StringValue": "BATCH_COMPLETED"},
        },
    )


def mark_item_done(batch_id: str, item_id: str) -> None:
    first_time = try_register_item_once(batch_id, item_id, state="DONE", ttl=ttl_days(14))
    if not first_time:
        return  # duplicata: não conta

    expected, done, failed = increment_batch_counters(batch_id, done_inc=1)

    # check local: done+failed chegou no expected?
    if (done + failed) == expected:
        if try_close_batch_if_all_finished(batch_id):
            publish_batch_completed(batch_id, expected, done, failed)


def mark_item_failed(batch_id: str, item_id: str) -> None:
    first_time = try_register_item_once(batch_id, item_id, state="FAILED", ttl=ttl_days(14))
    if not first_time:
        return

    expected, done, failed = increment_batch_counters(batch_id, failed_inc=1)

    if (done + failed) == expected:
        if try_close_batch_if_all_finished(batch_id):
            publish_batch_completed(batch_id, expected, done, failed)
