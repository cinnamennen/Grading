from __future__ import print_function

from time import sleep

import pymongo
from sshtunnel import SSHTunnelForwarder

student_names = [
#    removed
]
labs = [
    "lab0",
    "lab1",
    "lab2",
    "lab3",
    # "lab4",
    # "lab5",
    # "lab6",
    # "lab7",
    # "lab8",
    # "lab8",
    # "labA",
    # "labB"
]
with SSHTunnelForwarder(
        ("MONGO_SERVER_IP", 22),
        ssh_username="mongo_server_username",
        ssh_pkey="/home/USER/.ssh/KEYFILE",
        remote_bind_address=("localhost", 27017),
        local_bind_address=('0.0.0.0', 10022)
) as tunnel:
    sleep(2)
    with pymongo.MongoClient('0.0.0.0', port=10022) as client:
        sleep(1)
        print("netid,", ",".join(labs))
        # code starts here
        gradebook = client['grades']
        for student in student_names:
            print(student, " ", end="")
            for lab in labs:
                lab_grades = gradebook[lab]

                student_grade = lab_grades.find_one({
                    "_id": student
                })
                if student_grade is None:
                    print("Could not find a grade for", lab)
                else:
                    print("," + str(student_grade['grade']), end="")
            print("\n")
