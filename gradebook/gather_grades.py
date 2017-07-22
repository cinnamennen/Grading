#!/home/TA_NET_ID/.virtualenvs/grading/bin/python
import math
import pymongo
from sshtunnel import SSHTunnelForwarder
from tqdm import tqdm

student_names = [
#     student ids would be here
]
labs = [
    "lab0",
    "lab1",
    "lab2",
    "lab3",
    "lab5",
    "lab7",
    "lab8",
    "laba",
    "labb"
]


with SSHTunnelForwarder(
        ("MONGO_SERVER_IP", 22),
        ssh_username="mongo_server_username",
        ssh_pkey="/home/USER/.ssh/KEYFILE",
        remote_bind_address=("localhost", 27017),
        local_bind_address=('0.0.0.0', 10022)
) as tunnel:
    client = pymongo.MongoClient('0.0.0.0', port=10022)
    # code starts here
    gradebook = client['grades']
    final = gradebook['final']
    for student in tqdm(student_names):
        to_insert = {"_id": student}
        for lab in tqdm(labs):
            section = gradebook[lab]
            f = section.find_one({
                "_id": student
            })
            if f is None:
                print("ERROR", student, lab)
            else:
                to_insert[lab] = int(math.ceil(f['grade']))
        try:
            final.insert_one(to_insert)
        except:
            pass
