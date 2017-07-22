import tarfile
from operator import itemgetter
from time import sleep

import gridfs
import pymongo
from sshtunnel import SSHTunnelForwarder

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
            processingdb = client['processing']
            processed = client['processed']
            filedb = client['files']
            sourcedb = client['source']
            message_collection = processingdb['needs_processing']

            message_cursor = message_collection.find({})
            done = []
            for message in message_cursor:
                lab_number = message['lab']
                netid = message['netid']
                submission = {
                    'time': message['time'],
                    'filename': message['filename'].replace('labA', 'laba').replace('labB', 'labb')
                }
                lab_collection = processed['lab' + lab_number]
                student = lab_collection.find_one({
                    '_id': netid
                })

                submissions_handle = student['submissions']
                assert isinstance(submissions_handle, list)
                submissions_handle.append(submission)
                to_update = sorted(submissions_handle, key=lambda k: k['time'], reverse=True)
                student['submissions'] = to_update
                lab_collection.save(student)
                done.append(message['_id'])

            for item in done:
                message_collection.delete_one({
                    '_id': item
                })


if __name__ == '__main__':
    main()
