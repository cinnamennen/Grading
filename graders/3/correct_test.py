#!/home/TA_NET_ID/.virtualenvs/grading/bin/python
from __future__ import print_function

import tarfile

import os
from time import sleep

import gridfs
import pymongo
import shutil

from sshtunnel import SSHTunnelForwarder
import subprocess

local_address = '0.0.0.0'
port = 10022
path_join = os.path.join("..", "..", "..", "..", "..", "scratch", "TA_NET_ID")
lab_number = '3'
source_name = "huff_dec.c"
lab = 'lab' + lab_number
inspect = True

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
        tars = gridfs.GridFS(file_db, collection=lab)

        grade_cursor = grades.find({
            "correct": {"$exists": False}
        })
        for needs_grading in grade_cursor:
            student = processed.find_one({
                "_id": needs_grading["_id"]
            })
            if student is None:
                print("couldn't find a submission for", needs_grading['_id'])
                continue

            student_path = os.path.join(join, lab + "_360_" + student['_id'])
            try:
                os.makedirs(student_path)
            except OSError:
                shutil.rmtree(student_path)
                os.makedirs(student_path)

            os.chdir(student_path)

            # Do the tar stuff

            tar_filename = student['submissions'][0]['filename']
            grid_out = tars.find_one({
                '_id': tar_filename
            }, no_cursor_timeout=True)

            with tarfile.open(mode="r:gz", fileobj=grid_out) as tar:
                assert isinstance(tar, tarfile.TarFile)
                tar.extractall(path="..")
            try:
                subprocess.check_call(["make"], stdout=FNULL, stderr=FNULL)
            except subprocess.CalledProcessError:
                print("compilation error", student['_id'])
                if inspect:
                    while "y" not in raw_input("Ready to continue? "):
                        pass
                else:
                    continue

            output = subprocess.check_output(["/home/plank/cs360/labs/" + lab + "/gradeall"])

            n_correct = output.count('is correct.')

            needs_grading['correct'] = int(n_correct)
            grades.save(needs_grading)

            shutil.rmtree(student_path)

            # break
