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
            "quality": {"$exists": False}
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
            if source is None:
                print("no source from", needs_grading["_id"])
                continue

            student_path = os.path.join(join, student['_id'])
            try:
                os.makedirs(student_path)
            except OSError:
                shutil.rmtree(student_path)
                os.makedirs(student_path)

            os.chdir(student_path)

            with open("chain_heal.c", "w") as f:
                f.write(source.read())

            subprocess.call(["clear"])
            subprocess.call(["clear"])
            subprocess.call(["clear"])

            for x in range(10):
                sys.stdout.write('\r')
                sys.stdout.flush()

            print("=" * 80)
            print("=" * 80)
            print("=" * 80)
            print("=" * 80)
            print("=" * 80)

            subprocess.call(["pygmentize", "-g", "chain_heal.c"])

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
                q_i = raw_input("Quality (0-5): ")
                quality = RepresentsInt(q_i)
                if quality is False:
                    if q_i == 'q':
                        done = True
                    elif q_i == 'c':
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

            needs_grading['quality'] = quality + comments
            if quality + comments != 10:
                needs_grading['reasoning'] = raw_input("Why? ")
            else:
                needs_grading['reasoning'] = 'No problems'
            grades.save(needs_grading)
