#!/home/TA_NET_ID/.virtualenvs/grading/bin/python

import base64
import mimetypes
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep

import httplib2
import os
import pymongo
import sys
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.client import Storage
from oauth2client.file import Storage
from sshtunnel import SSHTunnelForwarder
from tqdm import tqdm
try:
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None
    argparse = None

from apiclient import errors

SCOPES = 'https://mail.google.com/'
CLIENT_SECRET_FILE = '../../collection/client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'

m = """
{_id},

Your lab grades are as follows:
lab0 lab1 lab2 lab3 lab5 lab7 lab8 laba labb
{lab0:>4} {lab1:>4} {lab2:>4} {lab3:>4} {lab5:>4} {lab7:>4} {lab8:>4} {laba:>4} {labb:>4}

If this is not consistent with the lab grade emails you have received, please email me and let me know
"""


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


credentials = get_credentials()
http = credentials.authorize(httplib2.Http())
my_service = discovery.build('gmail', 'v1', http=http)


def SendMessage(service, user_id, message):
    """Send an email message.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      message: Message to be sent.

    Returns:
      Sent Message.
    """
    try:
        message = (service.users().messages().send(userId=user_id, body=message)
                   .execute())
        # print 'Message Id: %s' % message['id']
        return True
    except errors.HttpError, error:
        # print 'An error occurred: %s' % error
        return False


def CreateMessage(sender, to, subject, message_text):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.

    Returns:
      An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string())}


def CreateMessageWithAttachment(sender, to, subject, message_text, file_dir,
                                filename):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.
      file_dir: The directory containing the file to be attached.
      filename: The name of the file to be attached.

    Returns:
      An object containing a base64url encoded email object.
    """
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    msg = MIMEText(message_text)
    message.attach(msg)

    path = os.path.join(file_dir, filename)
    content_type, encoding = mimetypes.guess_type(path)

    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    if main_type == 'text':
        fp = open(path, 'rb')
        msg = MIMEText(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'image':
        fp = open(path, 'rb')
        msg = MIMEImage(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'audio':
        fp = open(path, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=sub_type)
        fp.close()
    else:
        fp = open(path, 'rb')
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        fp.close()

    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(msg)

    return {'raw': base64.urlsafe_b64encode(message.as_string())}


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

    cursor = lab.find({
        "$or": [{"emailed": False}, {"emailed": {"$exists": False}}]
    })

    for student in tqdm(cursor, total=cursor.count()):

        email_text = m.format(**student)
        # print (email_text)
        # continue

        message = CreateMessage("TA_NET_ID@vols.utk.edu", student['_id'] + "@vols.utk.edu",
                                "Final Lab Grades",
                                email_text)

        success = SendMessage(my_service, 'me', message)
        if success:
            student['emailed'] = True
            lab.save(student)
        else:
            student['emailed'] = False
            lab.save(student)
