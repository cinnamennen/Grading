from time import sleep
import datetime
import pytz
import bson
import datetime
import pymongo
import pytz
from pymongo.errors import DuplicateKeyError
from sshtunnel import SSHTunnelForwarder
import re

local_address = '0.0.0.0'
port = 10022


def main():
    with SSHTunnelForwarder(
            ("MONGO_SERVER_IP", 22),
            ssh_username="mongo_server_username",
            ssh_pkey="/home/USER/.ssh/KEYFILE",
            remote_bind_address=("localhost", 27017),
            local_bind_address=(local_address, port)
    ) as tunnel:
        sleep(1)

        with pymongo.MongoClient(local_address, port=port) as client:
            # code starts here
            db = client['processing']
            processed = client['processed']
            file_collection = db['files']
            message_collection = db['needs_processing']
            message_cursor = message_collection.find({})
            for message in message_cursor:
                m = re.match(r"lab(?P<number>[\dabAB]*)\.360\.(?P<netid>.*)\.(?P<time>\d*)\.tgz", message['filename'])
                if m is None:
                    print (message['filename'])
                    continue
                if m.group('netid') != message['netid']:
                    print ("NETID does not match")
                    continue
                num = m.group('number')

                if num == 'A':
                    num = 'a'
                if num == 'B':
                    num = 'b'

                message['lab'] = num
                tz = pytz.timezone("US/Eastern")
                super_naive = datetime.datetime.utcfromtimestamp(float(m.group('time')))

                message['time'] = super_naive
                # print (message['netid'])
                # print (message['time'])
                message_collection.save(message)
                try:
                    processed['lab' + num].insert_one({
                        '_id': m.group('netid'),
                        'submissions': []
                    })
                except DuplicateKeyError:
                    pass
                try:
                    client['grades']['lab' + num].insert_one({
                        '_id': m.group('netid'),
                        'graded': False
                    })
                except DuplicateKeyError:
                    pass


if __name__ == '__main__':
    main()
