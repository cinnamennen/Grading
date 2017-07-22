#!/home/TA_NET_ID/.virtualenvs/grading/bin/python

from __future__ import print_function

from time import sleep

import datetime

import math
import pymongo
import pytz
from sshtunnel import SSHTunnelForwarder

from graders.lab5 import lab

no_late = datetime.datetime(2017, 3, 5, hour=23, minute=59, second=59,
                            tzinfo=pytz.timezone("US/Eastern")) + datetime.timedelta(minutes=5)
ten_late = datetime.datetime(2017, 3, 10, hour=23, minute=59, second=59,
                             tzinfo=pytz.timezone("US/Eastern")) + datetime.timedelta(minutes=5)
twenty_late = datetime.datetime(2017, 3, 12, hour=23, minute=59, second=59,
                                tzinfo=pytz.timezone("US/Eastern")) + datetime.timedelta(minutes=5)
reg_policy = datetime.datetime(2017, 3, 10, hour=23, minute=59, second=59,
                               tzinfo=pytz.timezone("US/Eastern")) + datetime.timedelta(minutes=5)

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
        for grade in grade_cursor:
            student = student_collection.find_one({"_id": grade['_id']})
            if student is None:
                # print("no submission from", grade['_id'])
                continue

            submission_time = student['submissions'][0]['time']

            loc_dt = pytz.timezone("UTC").localize(submission_time)
            loc_dt = loc_dt.astimezone(tz=pytz.timezone("US/Eastern"))

            if late_tool(loc_dt, no_late) <= 0:
                grade['late'] = 0

            elif late_tool(loc_dt, ten_late) < 0:
                grade['late'] = 1
            else:
                print(grade["_id"], "submitted on", loc_dt - datetime.timedelta(minutes=5), late_tool(loc_dt, no_late))
                continue
            if True:
                pass
            elif late_tool(loc_dt, twenty_late) < 0:
                grade['late'] = 2
            else:
                grade['late'] = late_tool(loc_dt, reg_policy)

            # print("would set a late of", grade['late'], grade['_id'])
            # continue

            grading_collection.save(grade)
