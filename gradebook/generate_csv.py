#!/home/TA_NET_ID/.virtualenvs/grading/bin/python

from time import sleep

import csv
import pymongo
from sshtunnel import SSHTunnelForwarder
from tqdm import tqdm

with open('grades.csv', 'w') as csv_file:
    fieldnames = ['netid',
                  "lab0",
                  "lab1",
                  "lab2",
                  "lab3",
                  "lab5",
                  "lab7",
                  "lab8",
                  "laba",
                  "labb"]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

    with SSHTunnelForwarder(
            ("MONGO_SERVER_IP", 22),
            ssh_username="mongo_server_username",
            ssh_pkey="/home/USER/.ssh/KEYFILE",
            remote_bind_address=("localhost", 27017),
            local_bind_address=('0.0.0.0', 10022)
    ) as tunnel:
        sleep(1)
        c = pymongo.MongoClient('0.0.0.0', port=10022)
        # code starts here
        gradebook = c['grades']

        lab = gradebook['final']

        cursor = lab.find({})

        for student in tqdm(cursor, total=cursor.count()):
            del student['emailed']
            student['netid'] = student.pop('_id')
            writer.writerow(student)
            # print student
