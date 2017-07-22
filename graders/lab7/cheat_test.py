#!/home/TA_NET_ID/.virtualenvs/grading/bin/python

from __future__ import print_function
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from time import sleep

import gridfs
import pymongo
import shutil

import subprocess
from sshtunnel import SSHTunnelForwarder
from graders.lab7 import *

local_address = '0.0.0.0'
port = 10022


codes = []

# noinspection PyUnusedLocal
with SSHTunnelForwarder(
        ("MONGO_SERVER_IP", 22),
        ssh_username="mongo_server_username",
        ssh_pkey="/home/USER/.ssh/KEYFILE",
        remote_bind_address=("localhost", 27017),
        local_bind_address=(local_address, port)
) as tunnel:
    sleep(1)

    # print(os.system("cd /local_scratch"))
    # print(os.system("mkdir /local_scratch/360_grading"))
    # print (os.system("whoami"))

    path_join = os.path.join("..", "..", "..", "..", "..", "scratch", "TA_NET_ID")
    join = os.path.join(path_join, lab)
    try:
        os.makedirs(join)
    except OSError:
        pass
    os.chdir(join)
    FNULL = open(os.devnull, 'w')
    cmd = ["/home/TA_NET_ID/bin/moss", "-l", "c", "-m", "10"]

    with pymongo.MongoClient(local_address, port=port) as client:
        processed = client['processed'][lab]
        grades = client['grades'][lab]
        file_db = client['files']
        files = gridfs.GridFS(file_db, collection=lab)

        grade_cursor = grades.find({
        })
        for needs_grading in grade_cursor:
            student = processed.find_one({
                "_id": needs_grading["_id"],
                "source": {
                    "$exists": True
                }
            })
            if student is None:
                continue
            source = files.find_one({
                "_id": student['source']
            })

            name = student["_id"]
            assert isinstance(name, unicode)
            file_name = name.encode('ascii') + "_" + filename
            assert isinstance(file_name, str)
            with open(file_name, "w") as f:
                f.write(source.read())

            codes.append(file_name)

        cmd += codes

        subprocess.call(cmd)
