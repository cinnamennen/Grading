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
    """

    :type s: str
    """
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
    lab_number = '1'
    lab = 'lab' + lab_number
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
            "memory": {"$exists": False}

        })
        for needs_grading in grade_cursor:
            subprocess.call(["clear"])
            subprocess.call(["clear"])
            subprocess.call(["clear"])

            for x in range(10):
                sys.stdout.write('\r')
                sys.stdout.flush()

            student = processed.find_one({
                "_id": needs_grading["_id"]
            })
            if student is None:
                print("couldn't find a submission for", needs_grading['_id'])
                continue
            source = files.find_one({
                "_id": student['source']
            })

            assert isinstance(source, gridfs.GridOut)

            student_path = os.path.join(join, student['_id'])
            try:
                os.makedirs(student_path)
            except OSError:
                shutil.rmtree(student_path)
                os.makedirs(student_path)

            os.chdir(student_path)

            source_read = source.read()
            with open("famtree.c", "w") as f:
                f.write(source_read)

            with open(os.path.join("/home", "TA_NET_ID", "grading", "graders", lab_number, "makefile")) as f:
                l = f.read()

            with open("makefile", "w") as f:
                f.write(l)

            try:
                subprocess.check_call(["make"], stdout=FNULL, stderr=FNULL)
            except subprocess.CalledProcessError:
                print("compilation error", student['_id'])
                while "y" not in raw_input("Ready to continue? "):
                    pass
                continue

            vstring = "no leaks are possible"

            gradefile = open("/home/plank/cs360/labs/lab1/Gradescript-Examples/090.txt", "r")

            try:
                output = subprocess.check_output(["valgrind", "--leak-check=yes", "./famtree"],
                                                 stdin=gradefile)
            except subprocess.CalledProcessError:
                output = "BAD THING"

            pass_valgrind = output.find(vstring)

            if pass_valgrind:
                print(student["_id"], "passed")
                needs_grading["memory"] = 5
                needs_grading['memory_reasoning'] = 'No problems'

            else:
                print(student["_id"], "didn't pass valgrind")
                if "free" not in source_read and "malloc" in source_read:
                    print("no free's, and they malloc'd")
                    needs_grading['memory_reasoning'] = 'You call malloc, but never free'
                    needs_grading['memory'] = 3

                    print("at least they called free")

                else:
                    print("need to hand grade")
                    while "y" not in raw_input("Ready to continue? "):
                        pass

                    command = subprocess.Popen("pygmentize famtree.c | perl -e 'print ++$i.\" $_\" for <>'",
                                               shell=True)

                    command.wait()

                    done = False
                    comments = 0
                    quality = 0
                    cont = False

                    while not done:
                        q_i = raw_input("Quality (0-5): ")
                        quality = RepresentsInt(q_i)
                        if quality is False:
                            if q_i == 'q':
                                done = True
                            elif q_i == 'c':
                                cont = True
                                break
                            continue
                        else:
                            assert isinstance(quality, int)
                            needs_grading["memory"] = quality
                        break

                    if done:
                        os.chdir(join)
                        shutil.rmtree(student_path)
                        break
                    elif cont:
                        os.chdir(join)
                        shutil.rmtree(student_path)
                        continue

                    if quality != 5:
                        s = raw_input("Why? ")
                        if s == 'c' or s == 'q':
                            break
                        needs_grading['memory_reasoning'] = s

                    else:
                        needs_grading['memory_reasoning'] = 'Make sure you pass valgrind for future labs'

            grades.save(needs_grading)

            shutil.rmtree(student_path)

            # break
