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
import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from graders.labb import *

inspect = False


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
        files = gridfs.GridFS(file_db, collection=lab)
        tars = gridfs.GridFS(file_db, collection=lab)

        grade_cursor = grades.find({
            "memory": {"$exists": False},
            "correct": {"$exists": True}

        })
        # print("working on", grade_cursor.count())
        # while "y" not in raw_input("Ready to continue? "):
        #     pass

        with tqdm.tqdm(total=grade_cursor.count()) as pbar:
            assert (isinstance(pbar, tqdm.tqdm))
            # print(type(pbar))
            for needs_grading in grade_cursor:
                pbar.set_description(needs_grading['_id'])
                pbar.refresh()
                needs_grading["memory"] = 5
                needs_grading['memory_reasoning'] = 'No problems'
                grades.save(needs_grading)
                # subprocess.call(["chmod", '-R', '700', '.'])
                # shutil.rmtree(student_path)
                pbar.update(1)
                continue

                if inspect:
                    subprocess.call(["clear"])
                    subprocess.call(["clear"])
                    subprocess.call(["clear"])

                    for x in range(10):
                        sys.stdout.write('\r')
                        sys.stdout.flush()

                student = processed.find_one({
                    "_id": needs_grading["_id"]
                })

                if needs_grading["_id"] == "TA_NET_ID":
                    needs_grading["memory"] = 5
                    needs_grading['memory_reasoning'] = 'No problems'
                    grades.save(needs_grading)
                    subprocess.call(["chmod", '-R', '700', '.'])
                    shutil.rmtree(student_path)
                    pbar.update(1)
                    continue

                if student is None:
                    # print("couldn't find a submission for", needs_grading['_id'])
                    continue
                else:
                    # print("working with", student["_id"])
                    pass

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
                # try:
                #     subprocess.check_call(["make"], stdout=FNULL, stderr=FNULL)
                # except subprocess.CalledProcessError:
                #     # tqdm.tqdm.write("compilation error " + student['_id'])
                #     needs_grading['correct'] = 0
                #     if "special_comment" not in needs_grading:
                #         needs_grading['special_comment'] = "did not compile (memory test)"
                #     else:
                #         needs_grading['special_comment'] += ", did not compile (memory test)"
                #     needs_grading['memory'] = 0
                #
                #     if inspect:
                #         while "y" not in raw_input("Ready to continue? "):
                #             pass
                #     else:
                #         subprocess.call(["chmod", '-R', '700', '.'])
                #
                #         shutil.rmtree(student_path)
                #         pbar.update(1)
                #         grades.save(needs_grading)
                #         continue



                vstring = "no leaks are possible"

                # gradefile = open("/home/plank/cs360/labs/lab" + lab_number + "/Gradescript-Examples/" + "070" +
                # ".txt", "r")

                stderr1 = None
                stderr2 = None
                x = None
                output = ""
                # try:
                #     subprocess.Popen(["timeout", "1m", ], stdout=FNULL,
                #                      stderr=FNULL)
                # except:
                #     # print('failure')
                #     pass
                # print('ls')
                # subprocess.Popen(['ls'])
                # print("pwd")
                # subprocess.call(['pwd'])
                sleep(1)

                try:
                    command1 = ["timeout", "1m", "valgrind", "--leak-check=yes",
                                "/home/plank/cs360/labs/" + lab + "/gradescript", "90"]
                    p1 = subprocess.Popen(command1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    stdout1, stderr1 = p1.communicate()

                except subprocess.CalledProcessError:
                    # print(student['_id'], "failed")
                    # print("Output is", output)
                    # while raw_input("Ready to continue? "):
                    pass

                if p1.returncode == 124:
                    pbar.write("timed out")
                    needs_grading["memory"] = 0
                    needs_grading['memory_reasoning'] = 'Could not test'
                    grades.save(needs_grading)
                    subprocess.call(["chmod", '-R', '700', '.'])
                    shutil.rmtree(student_path)
                    pbar.update(1)
                    continue

                try:
                    x = stderr1.index(vstring)
                except ValueError:
                    x = -1
                finally:
                    # print("x is at", x)
                    pass

                # pass_valgrind = output.find(vstring)
                # print(student["_id"])

                if x >= 0:
                    # print(student["_id"], "passed")
                    needs_grading["memory"] = 5
                    needs_grading['memory_reasoning'] = 'No problems'
                    # pbar.write("got one")

                else:
                    # print("here", x, stderr1)

                    # print(student["_id"], "didn't pass valgrind")
                    try:
                        with open(filename, "r") as source:
                            source_read = source.read()
                    except IOError:
                        needs_grading['memory_reasoning'] = 'You didn\'t pass the memory test'
                        needs_grading['memory'] = 0
                        grades.save(needs_grading)
                        subprocess.call(["chmod", '-R', '700', '.'])
                        shutil.rmtree(student_path)
                        pbar.update(1)
                        continue
                    allocated = any(word in source_read for word in ['malloc', 'strdup', 'strndup'])
                    free = "free(" in source_read
                    if not free and allocated:
                        pbar.write("no free's, and they malloc'd")
                        needs_grading['memory_reasoning'] = 'You call malloc, but never free'
                        needs_grading['memory'] = 0
                    else:
                        pbar.write("at least they called free")
                        needs_grading['memory_reasoning'] = 'Make sure you pass valgrind for future labs'
                        needs_grading["memory"] = 3

                        pass

                        # print("need to hand grade", free, allocated)
                        # print("source is")
                        # print(source_read)
                        if inspect:
                            while "y" not in raw_input("Ready to inspect? "):
                                pass

                            command = subprocess.Popen(
                                "pygmentize " + filename + " | perl -e 'print ++$i.\" $_\" for <>'",
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
                                subprocess.call(["chmod", '-R', '700', '.'])
                                shutil.rmtree(student_path)
                                break
                            elif cont:
                                os.chdir(join)
                                subprocess.call(["chmod", '-R', '700', '.'])
                                shutil.rmtree(student_path)
                                continue

                            if quality != 5:
                                s = raw_input("Why? ")
                                if s == 'c' or s == 'q':
                                    break
                                needs_grading['memory_reasoning'] = s

                            else:
                                needs_grading['memory_reasoning'] = 'Make sure you pass valgrind for future labs'

                # while raw_input("Ready to continue? "):
                #     pass
                grades.save(needs_grading)
                subprocess.call(["chmod", '-R', '700', '.'])
                shutil.rmtree(student_path)
                pbar.update(1)

                # break
