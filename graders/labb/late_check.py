#!/home/TA_NET_ID/.virtualenvs/grading/bin/python

from __future__ import print_function

import os
from time import sleep

import datetime

import math
import pymongo
import pytz
import sys
import tqdm
from sshtunnel import SSHTunnelForwarder

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from graders.labb import lab

duedate = datetime.datetime(2017, 4, 28, hour=23, minute=59, second=59, tzinfo=pytz.timezone("US/Eastern"))
duedate += datetime.timedelta(hours=72)
duedate += datetime.timedelta(minutes=5)


# late_duedate = datetime.datetime(2017, 1, 30, minute=4, tzinfo=pytz.timezone("US/Eastern")) - duedate
# print(late_duedate)
# print(late_duedate < datetime.timedelta(minutes=lab5))


local_address = '0.0.0.0'
port = 10022


def late_tool(loc_dt_meth, no_late_meth):
    lateness_meth = loc_dt_meth - no_late_meth
    late_days = lateness_meth.total_seconds() / datetime.timedelta(days=1).total_seconds()
    late_meth = math.ceil(late_days)
    late_meth = int(late_meth)
    return late_meth


with SSHTunnelForwarder(
        ("MONGO_SERVER_IP", 22),
        ssh_username="mongo_server_username",
        ssh_pkey="/home/USER/.ssh/KEYFILE",
        remote_bind_address=("localhost", 27017),
        local_bind_address=(local_address, port)
) as _:
    sleep(1)
    with pymongo.MongoClient(local_address, port=port) as client:

        grading_collection = client['grades'][lab]
        student_collection = client['processed'][lab]

        late = 0
        fine = 0
        grade_cursor = grading_collection.find({
            "late": {"$exists": False}
        })
        with tqdm.tqdm(total=grade_cursor.count()) as pbar:
            for grade in grade_cursor:
                student = student_collection.find_one({"_id": grade['_id']})
                if student is None:
                    # print("no submission from", grade['_id'])
                    grade['late'] = 0
                    grade['correct'] = 0
                    grade['memory'] = 0
                    grade['memory_reasoning'] = "No submission"
                    grade['comment_reasoning'] = "No submission"
                    grade['comment'] = 0
                    grading_collection.save(grade)
                    pbar.update(1)

                    continue
                pbar.set_description(grade['_id'])

                submission_time = student['submissions'][0]['time']

                loc_dt = pytz.timezone("UTC").localize(submission_time)
                loc_dt = loc_dt.astimezone(tz=pytz.timezone("US/Eastern"))
                lateness = loc_dt - duedate
                late_days = lateness.total_seconds() / datetime.timedelta(days=1).total_seconds()
                late = math.ceil(late_days)
                late = int(late)

                if lateness < datetime.timedelta(minutes=0):
                    grade['late'] = 0
                    # print(student['_id'], "is fine", lateness, loc_dt)
                    fine += 1
                else:
                    # print(lateness, student['_id'], late)
                    grade['late'] = late
                    late += 1

                grading_collection.save(grade)
                pbar.update(1)
