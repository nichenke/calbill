""" Use Google Calendar to build up time tracking for invoices.

Follow this to setup authentication:
- https://developers.google.com/api-client-library/python/start/get_started

- new project
- enable calendar API
- Download 'client_id.json' after adding cli tool credentials
- rename to credentials.json
- program will use browser to auth the first time, storing that in token.json

Getting Started with Calendar API:
- https://developers.google.com/calendar/overview

API Explorer:
- https://developers.google.com/apis-explorer/?hl=en_US#p/calendar/v3/calendar.calendarList.list?_h=1&

"""

from __future__ import print_function
import datetime
from collections import defaultdict

from dateutil import parser
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import pytz

WANTED_CAL = 'Cray Contracting'

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'


def billing_weeks():
    """ Generate tuple of timeMin, timeMax pairs that represent a billing week.

    NOTE: Hardcoding the billing start as Sept 26, 2018.
    """
    timezone = pytz.timezone('US/Mountain')
    now = datetime.datetime.now(timezone)
    start = datetime.datetime(2018, 9, 26, tzinfo=timezone)

    while True:
        end = start + datetime.timedelta(7)
        if end > now:
            break

        yield (start.isoformat(), end.isoformat())

        start = end


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))

    # Get list of calendars, looking for our desired calendar
    print('Getting list of calendars')
    result = service.calendarList().list().execute()

    calendars = result.get('items', [])
    cal_id = None
    for cal in calendars:
        if cal['summary'] == WANTED_CAL:
            cal_id = cal['id']
            print('Found {0} at id {1}'.format(WANTED_CAL, cal_id))
            break

    if not cal_id:
        print ('Could not find {0}'.format(WANTED_CAL))

    for timeMin, timeMax in billing_weeks():
        print('Getting events for {0}-{1}'.format(timeMin, timeMax))

        events_result = service.events().list(calendarId=cal_id, timeMin=timeMin, timeMax=timeMax,
                                              singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])

        this_week_total = 0.0

        if not events:
            print('No upcoming events found.')

        day_totals = defaultdict(int)
        for event in events:
            start = event['start'].get('dateTime')
            end = event['end'].get('dateTime')

            start = parser.parse(start)
            end = parser.parse(end)
            hours = (end - start).total_seconds() / 3600
            this_week_total += hours

            day_totals[start.date()] += hours

        for day, total in day_totals.items():
            # NOTE: format is for CVS pasting to excel, 2 empty colums between summary and hours.
            print("Coding - {0},,, {1}".format(day, total))

        print('Hours for week starting {0}: {1}'.format(timeMin, this_week_total))

if __name__ == '__main__':
    main()