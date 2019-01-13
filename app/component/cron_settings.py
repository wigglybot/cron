import os
from configobj import ConfigObj
from loguru import logger as log
import urllib.parse
import sys

log.remove()

dir_path = os.path.dirname(os.path.realpath(__file__))
CONFIG = ConfigObj(os.path.join(dir_path, "config.ini"))
ENVIRON = os.getenv("ENVIRON", CONFIG["config"]["ENVIRON"])

EVENT_STORE_URL = os.getenv("EVENT_STORE_URL", CONFIG[ENVIRON]["EVENT_STORE_URL"])
EVENT_STORE_HTTP_PORT = int(os.getenv("EVENT_STORE_HTTP_PORT", CONFIG[ENVIRON]["EVENT_STORE_HTTP_PORT"]))
EVENT_STORE_TCP_PORT = int(os.getenv("EVENT_STORE_TCP_PORT", CONFIG[ENVIRON]["EVENT_STORE_TCP_PORT"]))
EVENT_STORE_USER = os.getenv("EVENT_STORE_USER", CONFIG[ENVIRON]["EVENT_STORE_USER"])
EVENT_STORE_PASS = os.getenv("EVENT_STORE_PASS", CONFIG[ENVIRON]["EVENT_STORE_PASS"])

MONGO_URL = os.getenv("MONGO_URL", CONFIG[ENVIRON]["MONGO_URL"])
MONGO_PORT = int(os.getenv("MONGO_PORT", CONFIG[ENVIRON]["MONGO_PORT"]))
MONGO_USER = urllib.parse.quote_plus(os.getenv("MONGO_USER", CONFIG[ENVIRON]["MONGO_USER"]))
MONGO_PASS = urllib.parse.quote_plus(os.getenv("MONGO_PASS", CONFIG[ENVIRON]["MONGO_PASS"]))

LOGGER_LEVEL = os.getenv("LOGGER_LEVEL", CONFIG[ENVIRON]["LOGGER_LEVEL"])
LOGGER_FORMAT = '%(asctime)s [%(name)s] %(message)s'

V_MA = CONFIG["version"]["MAJOR"]
V_MI = CONFIG["version"]["MINOR"]
V_RE = CONFIG["version"]["REVISION"]
V_DATE = CONFIG["version"]["DATE"]
CODENAME = CONFIG["version"]["CODENAME"]

CRON = os.getenv("CRONTAB", CONFIG[ENVIRON]["CRONTAB"])

log.add(sys.stderr, level=LOGGER_LEVEL)


def version_fancy():
    return ''.join((
        "\n",
        " ______     ______     ______     __   __     ______     ______   ______ ", "\n",
        '/\  ___\   /\  == \   /\  __ \   /\ "-.\ \   /\  __ \   /\  == \ /\  ==', " \\",
        "        version: {0}".format("v%s.%s.%s" % (V_MA, V_MI, V_RE)), "\n",
        "\ \ \____  \ \  __<   \ \ \/\ \  \ \ \-.  \  \ \  __ \  \ \  _-/ \ \  _-/",
        "      code name: {0}".format(CODENAME), "\n",
        " \ \_____\  \ \_\ \_\  \ \_____\  \ \_\\\\", '"', "\_\  \ \_\ \_\  \ \_\    \ \_\  ",
        "   release date: {0}".format(V_DATE), "\n",
        "  \/_____/   \/_/ /_/   \/_____/   \/_/ \/_/   \/_/\/_/   \/_/     \/_/  "
        "      component: {0}".format(CONFIG["config"]["NAME"]), "\n"

    ))


log.info(version_fancy())
