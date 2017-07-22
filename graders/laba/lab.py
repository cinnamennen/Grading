#!/home/TA_NET_ID/.virtualenvs/grading/bin/python

from __future__ import print_function

import tarfile
from time import sleep

import gridfs
import os
import pymongo
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from graders.laba import lab, source
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
        message_collection = processingdb['needs_processing']
        message_cursor = message_collection.find({})

        tars = gridfs.GridFS(filedb, collection=lab)
        lab_collection = client['processed'][lab]
        student_cursor = lab_collection.find({
            "$or":
                [
                    {"source": {"$exists": False}}
                ]

        })

        for student in student_cursor:
            tar_filename = student['submissions'][0]['filename']
            grid_out = tars.find_one({
                '_id': tar_filename
            }, no_cursor_timeout=True)

            with tarfile.open(mode="r:gz", fileobj=grid_out) as tar:
                assert isinstance(tar, tarfile.TarFile)

                source_path = [x for x in tar.getnames() if x.endswith('.c')]
                if len(source_path) is not 1:
                    print("too many source files!", student['_id'], source_path, tar.getnames())
                    print(source_path)
                    continue
                source_path = source_path[0]
                member = tar.getmember(source_path)
                extract_source = tar.extractfile(member)
                assert isinstance(extract_source, tarfile.ExFileObject)
                source_file_id = tars.put(extract_source)
                student['source'] = source_file_id

                lab_collection.save(student)
    sleep(1)
