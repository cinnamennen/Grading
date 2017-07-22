#!/home/TA_NET_ID/.virtualenvs/grading/bin/python

from __future__ import print_function

import tarfile
from time import sleep

import gridfs
import pymongo
from sshtunnel import SSHTunnelForwarder

local_address = '0.0.0.0'
port = 10022

with SSHTunnelForwarder(
        ("MONGO_SERVER_IP", 22),
        ssh_username="mongo_server_username",
        ssh_pkey="/home/USER/.ssh/KEYFILE",
        remote_bind_address=("localhost", 27017),
        local_bind_address=(local_address, port)
) as _:
    sleep(1)

    with pymongo.MongoClient(local_address, port=port) as client:
        # code starts here
        processingdb = client['processing']
        filedb = client['files']
        sourcedb = client['source']
        message_collection = processingdb['needs_processing']
        message_cursor = message_collection.find({})

        tars = gridfs.GridFS(filedb, collection='lab1')
        lab_collection = client['processed']['lab1']
        student_cursor = lab_collection.find({
            "source": {"$exists": False}
        })

        for student in student_cursor:
            filename = student['submissions'][0]['filename']
            grid_out = tars.find_one({
                '_id': filename
            }, no_cursor_timeout=True)

            with tarfile.open(mode="r:gz", fileobj=grid_out) as tar:
                # print(tar.list())
                assert isinstance(tar, tarfile.TarFile)
                # ch = tar.extractfile()
                # print(tar.getnames())
                # print(tar.getmembers())

                path = [x for x in tar.getnames() if 'famtree.c' in x]
                if len(path) is not 1:
                    print("too many files!")
                    continue
                path = path[0]
                member = tar.getmember(path)
                extract = tar.extractfile(member)
                file_id = tars.put(extract)

                student['source'] = file_id
                lab_collection.save(student)
