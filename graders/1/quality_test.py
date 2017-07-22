#!/home/TA_NET_ID/.virtualenvs/grading/bin/python

from __future__ import print_function

import os
from time import sleep

import gridfs
import pymongo
import shutil

import subprocess

import sys
from sshtunnel import SSHTunnelForwarder


def RepresentsInt(s):
    try:
        int(s)
        return int(s)
    except ValueError:
        return False


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

    path_join = os.path.join("..", "..", "..", "..", "..", "scratch", "TA_NET_ID")
    lab = 'lab1'
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
        files = gridfs.GridFS(file_db, collection=lab)

        grade_cursor = grades.find({
            "comment": {"$exists": False}
        })
        for needs_grading in grade_cursor:
            student = processed.find_one({
                "_id": needs_grading["_id"]
            })

            if student is None:
                print("couldn't find a submission for", needs_grading['_id'])
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

            with open("famtree.c", "w") as f:
                f.write(source.read())

            subprocess.call(["clear"])
            subprocess.call(["clear"])
            subprocess.call(["clear"])

            for x in range(10):
                sys.stdout.write('\r')
                sys.stdout.flush()

            subprocess.call(["pygmentize", "-g", "famtree.c"])

            done = False
            comments = 0
            quality = 0
            cont = False
            while not done:
                c_i = raw_input("Commenting (0-5): ")
                comments = RepresentsInt(c_i)
                if comments is False:
                    if c_i == 'q':
                        done = True
                    elif c_i == 'c':
                        cont = True
                        break
                    continue
                break
            os.chdir(join)
            shutil.rmtree(student_path)

            if done:
                break
            elif cont:
                continue

            needs_grading['comment'] = comments
            if comments != 5:
                needs_grading['comment_reasoning'] = raw_input("Why? ")
            else:
                needs_grading['comment_reasoning'] = 'No commenting problems'
            grades.save(needs_grading)
