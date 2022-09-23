import os
import sys
import json
from datetime import datetime
import hashlib
import boto3
import logging
import traceback
from zapv2 import ZAPv2
import zap_common as z


logger = logging.getLogger()
logger.setLevel(logging.INFO if "PYTHONDEBUG" not in os.environ else logging.DEBUG)
streamer = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("level=%(levelname)s - %(message)s")
streamer.setFormatter(formatter)
logger.addHandler(streamer)


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
    spider_max = int(event.get("spider_max", int(os.environ.get("ZAP_SPIDER_MAX", 2))))
    ignore_alert_ids = event.get("ignore_alert_ids", default_ignore_ids)
    s3_key = None

    md5 = hashlib.md5()
    md5.update(target.encode("utf8"))
    target_hash = md5.hexdigest()

    if not target:
        logger.error(f"Had an invalid target")
        return {"error": "Not a valid target"}

    logger.info(f"About to scan target={target}")
    port = z.get_free_port()
    z.start_zap(port, ["-config", f"spider.maxDuration={spider_max}", "-dir", "/tmp"])
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
            logger.error(fh.read())

        logger.error(err)
        return {"error": "Could not fire up ZAP"}
    zap_version = zap.core.version
    access = z.zap_access_target(zap, target)
    # z.zap_spider(zap, target)

    logger.info(f"About to ajax-spider target={target}")

    z.zap_ajax_spider(zap, target, 2)
    logger.info(f"Starting to wait for passive scan")

    z.zap_wait_for_passive_scan(zap, timeout * 60)
    logger.info(f"Passve scan ... no longer waiting")

    alerts = z.zap_get_alerts(zap, target, ignore_alert_ids, {})
    urls = zap.core.urls()

    # Cleanup alerts and remove nodes
    zap.core.delete_all_alerts()
    for site in zap.core.sites:
        zap.core.delete_site_node(site)
    zap.core.run_garbage_collection()
    zap.core.shutdown()

    if "S3_BUCKET" in os.environ:
        bucket = os.environ["S3_BUCKET"]
        logger.info(f"Saving to s3 bucket={bucket}")
        s3_key = f"zap/results/{target_hash}/alerts.json"
        try:
            boto3.client("s3").put_object(
                Body=json.dumps(alerts, default=str),
                Bucket=bucket,
                Key=s3_key,
                ACL="private",
                Metadata={"target": target, "zap_version": zap_version},
            )
        except Exception as err:
            logger.error("Had error with s3")
            traceback.print_exc()

    return {
        "target_hash": target_hash,
        "start": start,
        "urls": urls,
        "s3_key": s3_key,
        "alerts_count": len(alerts),
    }


if __name__ == "__main__":
    response = handler({"target": sys.argv[1]})
    print(response)
