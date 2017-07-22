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
from graders.laba import *

local_address = '0.0.0.0'
port = random.randint(10000, 11000)
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

                tar_filename.replace('labA', 'laba')
                grid_out = tars.find_one({
                    '_id': tar_filename
                }, no_cursor_timeout=True)
                if grid_out is None:
                    tqdm.tqdm.write("no file", tar_filename, grid_out)
                    pbar.update(1)
                    continue

                with tarfile.open(mode="r:gz", fileobj=grid_out) as tar:
                    assert isinstance(tar, tarfile.TarFile)
                    tar.extractall(path="..")
                listdir = os.listdir(path_join + "/" + lab)
                folder = path_join + "/" + lab + "/" + listdir[-1]
                # print (listdir,folder)
                if "labA" in folder:
                    subprocess.call(["chmod", '-R', '700', '.'])
                    shutil.rmtree(student_path)
                    shutil.move(folder, folder.replace("labA", "laba"))
                    os.chdir(student_path)

                # subprocess.call(['pwd'])

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
                    else:
                        to_inspect += 1
                        subprocess.call(["chmod", '-R', '700', '.'])

                        shutil.rmtree(student_path)
                        pbar.update(1)
                        grades.save(needs_grading)
                        continue

                # print(x)
                pp = str(random.randint(13000, 15000))
                # subprocess.Popen(['ls'])
                try:
                    # subprocess.call(['pwd'])
                    # subprocess.call(['ls'])
                    execut = "./chat_server"
                    server = subprocess.Popen(
                        [execut, pp, "Bridge", "Baseball", "Politics",
                         "Video-Games", "Art",
                         "Music", "Movies", "Food", "Woodworking", "American-Idol"], stdout=FNULL, stderr=FNULL)
                    # print(execut)
                except OSError:
                    server.kill()
                    print(pp)
                    p = raw_input("pid")
                else:
                    p = None
                finally:
                    output = subprocess.check_output(
                        ["timeout", "15m", "/home/TA_NET_ID/grading/graders/laba/gradeall", "localhost", pp])
                    # print(output)
                    n_correct = output.count('is correct.')
                    server.kill()
                    # while "y" not in raw_input("Ready to continue? "):
                    #     pass
                    # n_correct = raw_input("Number correct: ")
                    if p is not None:
                        x = subprocess.Popen(["kill", "-9", p])
                        x.wait()

                needs_grading['correct'] = int(n_correct)
                grades.save(needs_grading)

                subprocess.call(["chmod", '-R', '700', '/scratch/TA_NET_ID'])

                shutil.rmtree(student_path)
                pbar.update(1)

                # break
        print("have", to_inspect, "to hand grade")
