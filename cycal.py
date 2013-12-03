#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import urllib2
import cookielib
import lxml.html

from settings import CYBOZU
from datetime import datetime, date
from icalendar import Calendar, Event
from icalendar.prop import vDatetime, vDate, vText

def connect(userid, password, gid, base_url):
    """ 接続する """

    # proxx
    #proxy = {'http':'http://localhost:8080/'}  
    #proxy_handler = urllib2.ProxyHandler(proxy)  
    #opener = urllib2.build_opener(proxy_handler)  
    #urllib2.install_opener(opener)  

    today = date.today()
    datestamp = '%s.%s.%s' % (today.year, today.month, 1)
    url = '%spage=ScheduleUserMonth&GID=%sUID=%s&Date=da.%s' % (base_url, gid,
            userid, str(datestamp))

    post = {
        '_System': 'login',
        '_Login': '1',
        'LoginMethod': '0',
        '_ID': userid,
        'Password': password
    }
    data = urllib.urlencode(post)

    cookiejar = cookielib.CookieJar()
    cookiejar_handler = urllib2.HTTPCookieProcessor(cookiejar)
    opener = urllib2.build_opener(cookiejar_handler)
    response = opener.open(url, data)

    if (response.code != 200):
        exit(0)

    return response

def get_html(response):
    """ htmlを取得する """

    html = response.read().decode('cp932').replace("\r", "")
    return html

def parse(html):
    """ htmlをパースする """

    root = lxml.html.fromstring(html)

    ical = Calendar()
    yyyymm = root.xpath('//td[@class="dateCell"]/b')[0].text
    year = yyyymm.split(u'年')[0]
    
    for events in root.find_class('eventcell'):

        for event_date in events.find_class('date'):
            event_date = event_date.text

        for event in events.find_class('eventInner'):
            event_line = {'time': '', 'detail': ''}
            ical_event = Event()

            for item in event:
                if (item.tag == 'li'):
                    event_line['time'] = ''
                    event_line['detail'] = item.find_class('event')[0].text

                if (item.tag == 'span'):
                    for time in item.find_class('eventDateTime'):
                        event_line['time'] = time.text

                    for detail in item.find_class('event'):
                        event_line['detail'] = detail.text

            mmdd = event_date.split('/')
            if (event_line['time'] != ''):
                startend_time = event_line['time'].split('-')
                start_time = startend_time[0]
                start_hhmm = start_time.split(':')
                if (len(startend_time) == 1):
                    event_line['time'] = event_line['time'].strip() + '-' + event_line['time'].strip()
                    end_time = startend_time[0]
                else:
                    end_time = startend_time[1]
                end_hhmm = end_time.split(':')
                ical_event.add('dtstart', datetime(int(year), int(mmdd[0]),
                    int(mmdd[1]), int(start_hhmm[0]), int(start_hhmm[1])))
                ical_event.add('dtend', datetime(int(year), int(mmdd[0]),
                    int(mmdd[1]), int(end_hhmm[0]), int(end_hhmm[1])))
            else:
                start_date = date(int(year), int(mmdd[0]), int(mmdd[1]))
                dtstart_prop = vDate(start_date)
                dtstart_prop.params['VALUE'] = vText('DATE')
                ical_event.add('dtstart',dtstart_prop)
                end_date = date(int(year), int(mmdd[0]), int(mmdd[1]))
                dtend_prop = vDate(end_date)
                dtend_prop.params['VALUE'] = vText('DATE')
                ical_event.add('dtend', dtend_prop)

            ical_event.add('summary', event_line['detail'])
            ical.add_component(ical_event)

    ical.add('version', '2.0')
    ical.add('prodid', '-//kuma//cycal.py//EN')

    return ical.to_ical()


if __name__ == '__main__':
    response = connect(CYBOZU['uid'], CYBOZU['pass'], CYBOZU['gid'], CYBOZU['url'])
    html = get_html(response)
    ical = parse(html)

    with open('cybozu.ics', 'w') as f:
        f.write(ical)

