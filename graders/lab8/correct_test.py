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
from graders.lab8 import *

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
        to_inspect = 0
        processed = client['processed'][lab]
        grades = client['grades'][lab]
        file_db = client['files']
        tars = gridfs.GridFS(file_db, collection=lab)

        grade_cursor = grades.find({
            "correct": {"$exists": False},

        })
        with tqdm.tqdm(total=grade_cursor.count()) as pbar:
            for needs_grading in grade_cursor:
                student = processed.find_one({
                    "_id": needs_grading["_id"]
                })
                assert isinstance(pbar, tqdm.tqdm)
                pbar.set_description(needs_grading['_id'])
                pbar.refresh()

                if student is None:
                    tqdm.tqdm.write("couldn't find a submission for " + needs_grading['_id'])
                    needs_grading['correct'] = 0
                    needs_grading['memory'] = 0
                    needs_grading['comment'] = 0
                    needs_grading['late'] = 0
                    needs_grading['memory_reasoning'] = "No submission"
                    needs_grading['comment_reasoning'] = "No submission"
                    needs_grading['special_comment'] = "No submission found"
                    subprocess.call(["chmod", '-R', '700', '.'])

                    pbar.update(1)
                    grades.save(needs_grading)
                    continue
                student_path = os.path.join(join, lab + "_360_" + student['_id'])

                try:
                    os.makedirs(student_path)
                except OSError:
                    subprocess.call(["chmod", '-R', '700', '.'])
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
                    tqdm.tqdm.write("compilation error " + student['_id'])
                    pass
                    # # needs_grading['correct'] = 0
                    # if "special_comment" not in needs_grading:
                    #     needs_grading['special_comment'] = "did not compile"
                    # else:
                    #     needs_grading['special_comment'] += ", did not compile"
                    #
                    # if inspect:
                    #     while "y" not in raw_input("Ready to continue? "):
                    #         pass
                    # else:
                    #     to_inspect += 1
                    #     subprocess.call(["chmod", '-R', '700', '.'])
                    #
                    #     shutil.rmtree(student_path)
                    #     pbar.update(1)
                    #     grades.save(needs_grading)
                    #     continue

                # output = subprocess.check_output(["/home/plank/cs360/labs/" + lab + "/gradeall"])
                # print (output)
                #
                # n_correct = output.count('is correct.')
                while "y" not in raw_input("Ready to continue? "):
                    pass
                n_correct = raw_input("Number correct: ")

                needs_grading['correct'] = int(n_correct)
                grades.save(needs_grading)

                subprocess.call(["chmod", '-R', '700', '.'])

                shutil.rmtree(student_path)
                pbar.update(1)

                # break
        print("have", to_inspect, "to hand grade")
