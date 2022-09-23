from __future__ import print_function
import os
import json
from datetime import datetime
import hashlib
import boto3
import logging
import traceback
from zapv2 import ZAPv2
import zap_common as z


logging.basicConfig(level=logging.DEBUG)


def handler(event={}, context={}):
    default_ignore_ids = [
        i
        for i in os.environ.get("ZAP_IGNORE_ALERT_IDS", "-1,50003,60000,60001").split(
            ","
        )
        if i
    ]
    target = event.get("target", "")
    timeout = event.get("timeout", int(os.environ.get("ZAP_TIMEOUT", 1)))
    ignore_alert_ids = event.get("ignore_alert_ids", default_ignore_ids)
    s3_key = None

    md5 = hashlib.md5()
    md5.update(target.encode("utf8"))
    target_hash = md5.hexdigest()

    if not target:
        return {"error": "Not a valid target"}

    port = z.get_free_port()
    z.start_zap(port, ["-config", "spider.maxDuration=2", "-dir", "/tmp"])
    start = datetime.today().strftime("%Y%m%d%H%I%s")
    zap = ZAPv2(
        proxies={
            "http": "http://localhost:" + str(port),
            "https": "http://localhost:" + str(port),
        }
    )
    try:
        z.wait_for_zap_start(zap, timeout * 60)
    except Exception as err:
        with open("/tmp/zap.out", "r") as fh:
            print(fh.read())

        print(err)
        return {"error": "Could not fire up ZAP"}
    zap_version = zap.core.version
    access = z.zap_access_target(zap, target)
    # z.zap_spider(zap, target)
    z.zap_ajax_spider(zap, target, 1)

    z.zap_wait_for_passive_scan(zap, timeout * 60)
    alerts = z.zap_get_alerts(zap, target, ignore_alert_ids, {})
    urls = zap.core.urls()

    # Cleanup alerts and remove nodes
    zap.core.delete_all_alerts()
    for site in zap.core.sites:
        zap.core.delete_site_node(site)
    zap.core.run_garbage_collection()
    zap.core.shutdown()

    if "S3_BUCKET" in os.environ:
        print("-- Saving to s3 bucket")
        s3_key = f"zap/results/{target_hash}/alerts.json"
        bucket = os.environ["S3_BUCKET"]
        try:
            boto3.client("s3").put_object(
                Body=json.dumps(alerts, default=str),
                Bucket=bucket,
                Key=s3_key,
                ACL="private",
                Metadata={"target": target, "zap_version": zap_version},
            )
        except Exception as err:
            print("-- Had error with s3")
            traceback.print_exc()

    return {
        "target_hash": target_hash,
        "start": start,
        "urls": urls,
        "s3_key": s3_key,
        "alerts_count": len(alerts),
    }
