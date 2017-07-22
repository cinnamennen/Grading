#!/home/TA_NET_ID/.virtualenvs/grading/bin/python

import shutil

import tarfile

import os
from time import sleep

import gridfs
import pymongo
import sys

from sshtunnel import SSHTunnelForwarder
import subprocess

import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from graders.laba import *

students = [
    "sbeztch1@vols.utk.edu",
    'wileliff@vols.utk.edu',
    "tdixon12@vols.utk.edu"

]
students = map(lambda x: x[:-13], students)

local_address = '0.0.0.0'
port = 10022
path_join = os.path.join("/", "scratch", "TA_NET_ID")

inspect = False

with SSHTunnelForwarder(
        ("MONGO_SERVER_IP", 22),
        ssh_username="mongo_server_username",
        ssh_pkey="/home/USER/.ssh/KEYFILE",
        remote_bind_address=("localhost", 27017),
        local_bind_address=(local_address, port)
) as _:
    sleep(1)

    join = os.path.join(path_join, lab)
    try:
        os.makedirs(join)
    except OSError:
        pass
    os.chdir(join)
    FNULL = open(os.devnull, 'w')

    with pymongo.MongoClient(local_address, port=port) as client:
        processed = client['processed'][lab]
        grades = client['grades'][lab]
        file_db = client['files']
        with tqdm.tqdm(total=len(students)) as pbar:
            for s in students:
                grade_cursor = grades.find_one({
                    "_id": s,
                    "correct": {"$exists": True},
                    "graded": True
                })
                if grade_cursor is not None:
                    del (grade_cursor['correct'])
                    grade_cursor['graded'] = False
                    grades.save(grade_cursor)
                else:
                    pbar.write("Error: " + s)
                pbar.update(1)
