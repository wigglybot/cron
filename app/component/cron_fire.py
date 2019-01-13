import sys
import argparse
from cron import Cron


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', action='store', dest='event_id', help='cron id')
    a = parser.parse_args(args)

    cronjob = Cron(a.event_id)
    cronjob.fetch_cron()
    cronjob.fire_cron()
    cronjob.delete_cron()


if __name__ == "__main__":
    main(sys.argv[1:])
