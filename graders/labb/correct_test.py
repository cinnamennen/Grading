#!/home/TA_NET_ID/.virtualenvs/grading/bin/python


import shutil

import tarfile

import os
from time import sleep

import gridfs
import pymongo
import sys

import random
from sshtunnel import SSHTunnelForwarder
import subprocess

import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from graders.labb import *

local_address = '0.0.0.0'
port = random.randint(10000, 11000)
path_join = os.path.join("/", "scratch", "TA_NET_ID")

inspect = True
nice = True

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
                    needs_grading['special_comment'] = "No submission found"
                    needs_grading['memory_reasoning'] = "No submission"
                    needs_grading['comment_reasoning'] = "No submission"
                    subprocess.call(["chmod", '-R', '700', '/scratch/TA_NET_ID'])

                    pbar.update(1)
                    grades.save(needs_grading)
                    continue

                tar_filename = str(student['submissions'][0]['filename'])
                file_path = lab + "_360_" + student['_id']
                student_path = os.path.join(join, file_path)

                try:
                    os.makedirs(student_path)
                except OSError:
                    subprocess.call(["chmod", '-R', '700', '/scratch/TA_NET_ID'])
                    shutil.rmtree(student_path)
                    os.makedirs(student_path)

                os.chdir(student_path)
                # Do the tar stuff

                tar_filename.replace('labB', 'labb')
                grid_out = tars.find_one({
                    '_id': tar_filename
                }, no_cursor_timeout=True)
                if grid_out is None:
                    tqdm.tqdm.write("no file", tar_filename, grid_out)
                    pbar.update(1)
                    continue

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
                listdir = os.listdir(path_join + "/" + lab)
                folder = path_join + "/" + lab + "/" + listdir[-1]
                # print (listdir,folder)
                if "labB" in folder:
                    subprocess.call(["chmod", '-R', '700', '.'])
                    shutil.rmtree(student_path)
                    shutil.move(folder, folder.replace("labB", "labb"))
                    os.chdir(student_path)
                shutil.copy("/home/plank/cs360/labs/labb/bonding-driver.c", student_path)
                shutil.copy("/home/plank/cs360/labs/labb/bonding.h", student_path)
                shutil.copy("/home/plank/cs360/labs/labb/makefile", student_path)
                shutil.copy("/home/plank/cs360/labs/labb/bonding-example-1.c", student_path)
                shutil.copy("/home/plank/cs360/labs/labb/bonding-example-2.c", student_path)

                try:
                    x = subprocess.check_call(["make"], stdout=FNULL, stderr=FNULL)
                except subprocess.CalledProcessError:
                    tqdm.tqdm.write("compilation error " + student['_id'])
                    needs_grading['correct'] = 0
                    needs_grading['memory'] = 0
                    needs_grading['memory_comment'] = "did not compile"

                    if "special_comment" not in needs_grading:
                        needs_grading['special_comment'] = "did not compile"
                    else:
                        needs_grading['special_comment'] += ", did not compile"

                    if inspect:
                        while "y" not in raw_input("Ready to continue? "):
                            pass
                    elif nice:
                        to_inspect += 1
                        subprocess.call(["chmod", '-R', '700', '.'])

                        shutil.rmtree(student_path)
                        pbar.update(1)
                        continue
                    else:
                        to_inspect += 1
                        subprocess.call(["chmod", '-R', '700', '.'])

                        shutil.rmtree(student_path)
                        pbar.update(1)
                        grades.save(needs_grading)
                        continue

                # print(x)

                output = subprocess.check_output(
                    ["timeout", "15m", "/home/plank/cs360/labs/" + lab + "/gradeall"])
                # print(output)
                n_correct = output.count('is correct.')
                # while "y" not in raw_input("Ready to continue? "):
                #     pass
                # n_correct = raw_input("Number correct: ")

                needs_grading['correct'] = int(n_correct)
                grades.save(needs_grading)

                subprocess.call(["chmod", '-R', '700', '/scratch/TA_NET_ID'])

                shutil.rmtree(student_path)
                pbar.update(1)

                # break
        print("have", to_inspect, "to hand grade")
