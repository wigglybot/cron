from cron_settings import *
import asyncio
from photonpump import connect, exceptions
import json
import functools
import uuid
import requests
from crontab import CronTab


def run_in_executor(f):
    """
    wraps a blocking (non-asyncio) function to execute it in the loop as if it were an async func
    """

    @functools.wraps(f)
    def inner(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, functools.partial(f, *args, **kwargs))

    return inner


try:
    file_cron = CronTab(tabfile=CRON)
    log.info(f"found cron file at {CRON}")
except FileNotFoundError as e:
    log.warning(f"creating cron file at {CRON}")
    file_cron = CronTab()
    try:
        file_cron.write(CRON)
    except Exception as e:
        log.exception(e)


def int_conv(value):
    try:
        result = int(str(value))
    except:
        result = value
    return result


def _create(event):
    data = json.loads(event.data)
    try:
        job = file_cron.new(command=f'/usr/local/bin/python cron_fire.py -i {data["event_id"]}', comment=data["event_id"])
        job.setall(
            int_conv(data['schedule']['minutes']),
            int_conv(data['schedule']['hours']),
            int_conv(data['schedule']['month_day']),
            int_conv(data['schedule']['month'])
        )
        file_cron.write(CRON)
        return {"code": 200, "event": data}
    except Exception as _e:
        log.exception(_e)
        return {"code": 500, "event": data}


def _delete(event):
    try:
        data = json.loads(event.data)
    except Exception as _e:
        log.exception(_e)
        return {"code": 500, "event": _e}
    try:
        _iter = file_cron.find_comment(data['event_id'])
        file_cron.remove(_iter)
        file_cron.write(CRON)
        return {"code": 204, "event": data}
    except Exception as _e:
        log.exception(_e)
        return {"code": 500, "event": _e}


@run_in_executor
def create_response(event):
    # here we're going to update the system cron using the data,
    """
    {
      "delete_completed": true,
      "event_id": "some_event_id",
      "schedule": {
        "minutes": "5",
        "hours": "11",
        "month": "1",
        "month_day": "1"
      },
      "target_stream": "dialogue",
      "target_type": "test",
      "target_event": {
        "test": "test_event",
        "event_id"
      }
    }
    """
    cron_action = {
        "put": _create,
        "delete": _delete
    }
    return cron_action[event.type](event)


@run_in_executor
def post_to_cron_stream(event, result_text):
    event_data = json.loads(event.data)
    headers = {
        "ES-EventType": f"cron_{event.type}",
        "ES-EventId": str(uuid.uuid1())
    }
    requests.post(
        "http://%s:%s/streams/cron" % (EVENT_STORE_URL, EVENT_STORE_HTTP_PORT),
        headers=headers,
        json={"event_id": event_data["event_id"], "response": result_text}
    )


def meets_criteria(event) -> bool:
    """
    :param data object from event:
    :return: bool based on whether this component should process the event object
    """
    return event.type == "put" or \
        event.type == "get" or \
        event.type == "delete"


async def create_subscription(subscription_name, stream_name, conn):
    await conn.create_subscription(subscription_name, stream_name)


async def cron_fn():
    _loop = asyncio.get_event_loop()
    async with connect(
            host=EVENT_STORE_URL,
            port=EVENT_STORE_TCP_PORT,
            username=EVENT_STORE_USER,
            password=EVENT_STORE_PASS,
            loop=_loop
    ) as c:
        await c.connect()
        try:
            await create_subscription("cron-d", "cron", c)
        except exceptions.SubscriptionCreationFailed as e:
            if e.message.find("already exists"):
                log.info("cron dialogue subscription found.")
            else:
                log.exception(e)
        dialogue_stream = await c.connect_subscription("cron-d", "cron")
        async for event in dialogue_stream.events:
            if meets_criteria(event):
                log.debug("cron_fn() responding to: %s" % json.loads(event.data))
                try:
                    await post_to_cron_stream(event, await create_response(event))
                    await dialogue_stream.ack(event)
                except Exception as e:
                    log.exception(e)
            else:
                await dialogue_stream.ack(event)


if __name__ == "__main__":
    asyncio.set_event_loop(asyncio.new_event_loop())
    mainloop = asyncio.get_event_loop()
    mainloop.run_until_complete(cron_fn())
