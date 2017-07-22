import pymongo
from sshtunnel import SSHTunnelForwarder

student_names = [
    # removed
]
labs = [
    # "lab0",
    # "lab1",
    # "lab2",
    # "lab3",
    # "lab4",
    # "lab5",
    # "lab6",
    # "lab7",
    # "lab8",
    # "lab8",
    # "laba",
    # "labb"
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
    for lab in labs:
        section = gradebook[lab]
        for student in student_names:
            f = section.find_one({
                "_id": student
            })
            if f is None:
                section.insert_one(
                    {
                        "_id": student,
                        "graded": False
                    }
                )
            else:
                if 'graded' not in f:
                    f['graded'] = False
                    section.save(f)
