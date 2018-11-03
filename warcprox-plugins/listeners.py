'''
warcprox/kafkafeed.py - support for publishing information about archived
urls to apache kafka

Copyright (C) 2015-2016 Internet Archive

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
USA.
'''

import os
import time
import kafka
import datetime
import json
import logging
from hanzo import warctools
import threading
import requests
from io import StringIO
import warcprox
from typing import List


def cdx_line(entry):
    out = StringIO()
    out.write(entry['url'])
    out.write(' ')
    out.write(entry['start_time_plus_duration'][0:14])
    out.write(' ')
    out.write(entry['url'])
    out.write(' ')
    out.write(str(entry.get('content_type','')))
    out.write(' ')
    out.write(str(entry['status_code']))
    out.write(' ')
    out.write(entry['content_digest'])
    out.write(' - - ')
    out.write(str(entry['warc_length']))
    out.write(' ')
    out.write(str(entry['warc_offset']))
    out.write(' ')
    out.write(entry['warc_filename'])
    out.write('\n')
    line = out.getvalue()
    out.close()
    return line


def to_json(recorded_url: warcprox.warcproxy.RecordedUrl, records: List[warctools.WarcRecord]):
    # {"status_code":200,"content_digest":"sha1:3VU56HI3BTMDZBL2TP7SQYXITT7VEAJQ","host":"www.kaosgl.com","via":"http://www.kaosgl.com/sayfa.php?id=4427","account_id":"877","seed":"http://www.kaosgl.com/","warc_filename":"ARCHIVEIT-6003-WEEKLY-JOB171310-20150903100014694-00002.warc.gz","url":"http://www.kaosgl.com/resim/HomofobiKarsitiBulusma/trabzon05.jpg","size":29700,"start_time_plus_duration":"20150903175709637+1049","timestamp":"2015-09-03T17:57:10.707Z","mimetype":"image/jpeg","collection_id":"6003","is_test_crawl":"false","job_name":"6003-20150902172136074","warc_offset":856320200,"thread":6,"hop_path":"RLLLLLE","extra_info":{},"annotations":"duplicate:digest","content_length":29432}

    # Normal recorded response:
    if recorded_url.response_recorder:
        content_length = recorded_url.response_recorder.len - recorded_url.response_recorder.payload_offset
        payload_digest = warcprox.digest_str(
            recorded_url.payload_digest, True)
    else:
        # WARCPROX_WRITE_RECORD request:
        content_length = recorded_url.size
        payload_digest = records[0].get_header(b'WARC-Payload-Digest')

    # Deal with variation in content type:
    content_type = recorded_url.mimetype
    if content_type and content_type.find(" ") >= 0:
        content_type = "application/malformed-header"

    # Build the record:
    now = datetime.datetime.utcnow()
    d = {
        'url': recorded_url.url.decode('utf-8'),
        'host': recorded_url.host,
        'http_method': recorded_url.method,
        'status_code': recorded_url.status,
        'wire_bytes': recorded_url.size,
        'content_type': content_type,
        'content_digest': payload_digest.decode("utf-8"),
        'content_length': content_length,
        'start_time_plus_duration': '{:%Y%m%d%H%M%S}{:03d}+{}'.format(
            recorded_url.timestamp, recorded_url.timestamp.microsecond // 1000,
            int(recorded_url.duration.total_seconds() * 1000)),
        'annotations': 'duplicate:digest' if records[0].type == 'revisit' else '',
        'warc_filename': records[0].warc_filename,
        'warc_offset': records[0].offset,
        'warc_length': records[0].length,
        "warc_content_type": records[0].content_type.decode("utf-8"),
        "warc_type": records[0].type.decode("utf-8"),
        "warc_id": records[0].id.decode("utf-8"),
        'timestamp': '{:%Y-%m-%dT%H:%M:%S}.{:03d}Z'.format(now, now.microsecond // 1000)
    }

    # fields expected to be populated here are (for archive-it):
    # account_id, collection_id, is_test_crawl, seed, job_name
    if recorded_url.warcprox_meta and 'capture-feed-extra-fields' in recorded_url.warcprox_meta:
        for (k, v) in recorded_url.warcprox_meta['capture-feed-extra-fields'].items():
            d[k] = v

    return d


class KafkaCaptureFeed:
    logger = logging.getLogger('warcprox-plugins.listeners.CaptureFeed')

    def __init__(self):
        self.broker_list = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
        self.topic = os.environ["KAFKA_CRAWLED_TOPIC"]
        self.acks = int(os.environ.get("KAFKA_ACKS", "0"))
        self.__producer = None
        self._connection_exception = None
        self._lock = threading.RLock()

    def _producer(self):
        with self._lock:
            if not self.__producer:
                try:
                    # acks=0 to avoid ever blocking
                    self.__producer = kafka.KafkaProducer(
                            bootstrap_servers=self.broker_list, acks=self.acks)
                    if self._connection_exception:
                        logging.info('connected to kafka successfully!')
                        self._connection_exception = None
                except Exception as e:
                    if not self._connection_exception:
                        self._connection_exception = e
                        logging.error('problem connecting to kafka', exc_info=1)

        return self.__producer

    def notify(self, recorded_url: warcprox.warcproxy.RecordedUrl, records: List[warctools.WarcRecord]):

        if records[0].type not in (b'revisit', b'response', b'resource'):
            return

        topic = recorded_url.warcprox_meta.get('capture-feed-topic', self.topic)
        if not topic:
            return

        d = to_json(recorded_url,records)

        msg = json.dumps(d, separators=(',', ':')).encode('utf-8')
        self.logger.debug('feeding kafka topic=%r msg=%r', topic, msg)
        p = self._producer()
        if p:
            p.send(topic, msg)
        else:
            self.logger.warning("Could not find producer! Failed to send this message: " + msg)


class UpdateOutbackCDX:
    logger = logging.getLogger('warcprox-plugins.listeners.UpdateOutbackCDX')

    def __init__(self):
        self.endpoint = os.environ["CDXSERVER_ENDPOINT"]
        self.session = requests.Session()

    def notify(self, recorded_url, records):

        if records[0].type not in (b'revisit', b'response', b'resource'):
            self.logger.debug("Not sending record of type %s to the CDX Server" % records[0].type)
            return

        # FIXME! This pushes REVISIT records to the CDX Server with e.g. the original Content Type, not matching

        # Convert the record to the right form:
        d = to_json(recorded_url,records)
        cdx_11 = cdx_line(d)

        # POST it to the CDX server:
        sent = False
        tries = 0
        while not sent and tries < 5:
            r = self.session.post(self.endpoint, data=cdx_11.encode('utf-8'))
            if r.status_code == 200:
                sent = True
                self.logger.debug("POSTed to cdxserver: %s" % cdx_11)
            else:
                self.logger.error("Failed with %s %s\n%s" % (r.status_code, r.reason, r.text))
                self.logger.error("Failed submission was: %s" % cdx_11.encode('utf-8'))
                tries = tries + 1
                time.sleep(10)
        # Warn of failure:
        if not sent:
            self.logger.error("Failed to send record to CDX server for %s after %i attempts." % (d, tries))
