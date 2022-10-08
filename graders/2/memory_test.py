#!/home/TA_NET_ID/.virtualenvs/grading/bin/python

from __future__ import print_function

import tarfile

import os
from time import sleep

import gridfs
import pymongo
import shutil

import subprocess

import sys
from sshtunnel import SSHTunnelForwarder

inspect = True


def represents_int(string):
    """

    :type string: str
    """
    try:
        int(string)
        return int(string)
    except ValueError:
        return False


local_address = '0.0.0.0'
port = 10022
labname = "data_uncompress"
filename = labname + ".c"

with SSHTunnelForwarder(
        ("MONGO_SERVER_IP", 22),
        ssh_username="mongo_server_username",
        ssh_pkey="/home/USER/.ssh/KEYFILE",
        remote_bind_address=("localhost", 27017),
        local_bind_address=(local_address, port)
) as tunnel:
    sleep(1)

    path_join = os.path.join("..", "..", "..", "..", "..", "scratch", "TA_NET_ID")
    lab_number = '2'
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
        tars = gridfs.GridFS(file_db, collection=lab)

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
            try:
                subprocess.check_call(["make"], stdout=FNULL, stderr=FNULL)
            except subprocess.CalledProcessError:
                print("compilation error", student['_id'])
                if inspect:
                    while "y" not in raw_input("Ready to continue? "):
                        pass
                else:
                    continue

            with open(filename, "r") as source:
                source_read = source.read()

            vstring = "no leaks are possible"

            gradefile = open("/home/plank/cs360/labs/lab" + lab_number + "/Gradescript-Examples/" + "070" + ".txt", "r")

            output = ""
            try:
                output = subprocess.check_output(["valgrind", "--leak-check=yes", "./" + labname],
                                                 stdin=gradefile)
            except subprocess.CalledProcessError:
                pass

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
                        quality = represents_int(q_i)
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
