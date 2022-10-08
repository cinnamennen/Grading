#!/home/TA_NET_ID/.virtualenvs/grading/bin/python

from __future__ import print_function

import sys
from os import path

dirname = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
print(dirname)
sys.path.append(dirname)

import tarfile

import os
from time import sleep

import gridfs
import pymongo
import shutil

import subprocess

import sys
from sshtunnel import SSHTunnelForwarder

from graders.lab7 import *


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
            "comment": {"$exists": False}
        })
        for needs_grading in grade_cursor:
            student = processed.find_one({
                "_id": needs_grading["_id"]
            })

            if student is None:
                print("couldn't find a submission for", needs_grading['_id'])
                continue

            needs_grading['comment'] = 5
            needs_grading['comment_reasoning'] = 'No commenting problems'
            grades.save(needs_grading)

            continue

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
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(tar, path="..")

            subprocess.call(["pygmentize", "-g", filename])

            # done = False
            # comments = 0
            comments = 5
            done = True
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

            # subprocess.call(["pwd"])
            subprocess.call(["chmod", '-R', '700', '.'])
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
