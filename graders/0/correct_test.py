from __future__ import print_function

import os
from time import sleep

import gridfs
import pymongo
import shutil

import subprocess
from sshtunnel import SSHTunnelForwarder

local_address = '0.0.0.0'
port = 10022
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
    join = os.path.join(path_join, "lab0")
    try:
        os.makedirs(join)
    except OSError:
        pass
    os.chdir(join)
    FNULL = open(os.devnull, 'w')

    with pymongo.MongoClient(local_address, port=port) as client:
        processed = client['processed']['lab0']
        grades = client['grades']['lab0']
        file_db = client['files']
        files = gridfs.GridFS(file_db, collection='lab0')

        grade_cursor = grades.find({
            "correct": {"$exists": False}
        })
        for needs_grading in grade_cursor:
            student = processed.find_one({
                "_id": needs_grading["_id"]
            })
            if student is None:
                print("no submission from", needs_grading["_id"])
                continue

            source = files.find_one({
                "_id": student['source']
            })

            student_path = os.path.join(join, student['_id'])
            try:
                os.makedirs(student_path)
            except OSError:
                shutil.rmtree(student_path)
                os.makedirs(student_path)

            os.chdir(student_path)

            with open("chain_heal.c", "w") as f:
                f.write(source.read())

            with open(os.path.join("/home", "TA_NET_ID", "grading", "graders", "0", "makefile")) as f:
                l = f.read()

            with open("makefile", "w") as f:
                f.write(l)


            try:
                subprocess.check_call(["make"], stdout=FNULL, stderr=FNULL)
            except subprocess.CalledProcessError:
                print("compilation error")
                continue

            output = subprocess.check_output(["/home/plank/cs360/labs/lab0/gradeall"])

            n_correct = output.count('is correct.')

            needs_grading['correct'] = int(n_correct)
            grades.save(needs_grading)

            shutil.rmtree(student_path)

            # break
