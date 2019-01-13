from cron_settings import *
from pymongo import MongoClient
import uuid
import requests
import datetime
from crontab import CronTab


class Cron:
    def __init__(self, _id):
        self.job = None
        self._id = _id
        try:
            self.file_cron = CronTab(tabfile=CRON)
            log.info(f"found cron file at {CRON}")
        except FileNotFoundError as e:
            log.warning(f"creating cron file at {CRON}")
            self.file_cron = CronTab()
            try:
                self.file_cron.write(CRON)
            except Exception as e:
                log.exception(e)

    @staticmethod
    def post_to_stream(_type, data, stream):
        headers = {
            "ES-EventType": _type,
            "ES-EventId": str(uuid.uuid1())
        }
        requests.post(
            "http://%s:%s/streams/%s" % (EVENT_STORE_URL, EVENT_STORE_HTTP_PORT, stream),
            headers=headers,
            json=data
        )

    def fetch_cron(self):
        log.trace("enter")
        client = MongoClient('mongodb://%s:%s@%s' % (MONGO_USER, MONGO_PASS, MONGO_URL), MONGO_PORT)
        db = client["wigglybot_db"]
        dialogues = db.db["crons"]
        self.job = dialogues.find_one({'event_id': self._id})
        if self.job is None:
            self.post_to_stream(
                "cron_fire_failed",
                {
                    "event_id": self._id,
                    "fire": "failed"
                },
                "cron"
            )
            exit(1)
        else:
            self.post_to_stream(
                "cron_fire_found",
                {
                    "event_id": self._id,
                    "fire": "found"
                },
                "cron"
            )

    def fire_cron(self):
        try:
            self.post_to_stream(
                self.job["target_type"],
                self.job["target_event"],
                self.job["target_stream"]
            )
            self.post_to_stream(
                "cron_fire_success",
                {
                    "event_id": self._id,
                    "fire": str(datetime.datetime.now())
                },
                "cron"
            )
        except Exception as e:
            log.exception(e)
            self.post_to_stream(
                "cron_fire_failed",
                {
                    "event_id": self._id,
                    "fire": "failed"
                },
                "cron"
            )
            exit(1)

    def delete_cron(self):
        log.debug(f"{self._id} delete completed is {self.job['delete_completed']}")
        if self.job["delete_completed"]:
            self.post_to_stream(
                "delete",
                {
                    "event_id": self._id
                },
                "cron"
            )

