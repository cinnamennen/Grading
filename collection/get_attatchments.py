from __future__ import print_function

import base64
import pprint
from time import sleep

import gridfs
import httplib2
import os
import pymongo
from apiclient import discovery, errors
from gridfs.errors import FileExists
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from sshtunnel import SSHTunnelForwarder

try:
    # noinspection PyUnresolvedReferences
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
# SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
SCOPES = 'https://mail.google.com/'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'

pp = pprint.PrettyPrinter(indent=4)


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


def ListMessagesWithLabels(service, user_id, label_ids=None):
    """List all Messages of the user's mailbox with label_ids applied.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      label_ids: Only return Messages with these labelIds applied.

    Returns:
      List of Messages that have all required Labels applied. Note that the
      returned list contains Message IDs, you must use get with the
      appropriate id to get the details of a Message.
    """
    if label_ids is None:
        label_ids = []
    try:
        response = service.users().messages().list(userId=user_id,
                                                   labelIds=label_ids).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id,
                                                       labelIds=label_ids,
                                                       pageToken=page_token).execute()
            messages.extend(response['messages'])

        return messages
    except errors.HttpError as error:
        print('An error occurred: %s' % error)


def GetMessage(service, user_id, msg_id, printing=False):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()

        if printing:
            print('Message snippet: %s' % message['snippet'])

        return message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)


def GetAttachments(service, user_id, msg_id):
    """Get and store attachment from Message with given id.

    Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: ID of Message containing attachment.
    prefix: prefix which is added to the attachment filename on saving
    """
    files = []
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()

        for part in message['payload']['parts']:
            if part['filename']:
                if 'data' in part['body']:
                    data = part['body']['data']
                else:
                    att_id = part['body']['attachmentId']
                    att = service.users().messages().attachments().get(userId=user_id, messageId=msg_id,
                                                                       id=att_id).execute()
                    data = att['data']
                file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))

                files.append(file_data)
    except errors.HttpError as error:
        print('An error occurred: %s' % error)
    finally:
        return files


def ModifyMessage(service, user_id, msg_id, msg_labels, printing=False):
    try:
        message = service.users().messages().modify(userId=user_id, id=msg_id,
                                                    body=msg_labels).execute()

        label_ids = message['labelIds']

        if printing:
            print('Message ID: %s - With Label IDs %s' % (msg_id, label_ids))
        return message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)


def CreateMsgLabels(remove=None, add=None):
    """Create object to update labels.

    Returns:
      A label update object.
    """
    if add is None:
        add = []
    if remove is None:
        remove = []
    return {'removeLabelIds': remove, 'addLabelIds': add}


def main():
    """Shows basic usage of the Gmail API.

    Creates a Gmail API service object and outputs a list of label names
    of the user's Gmail account.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    local_address = '0.0.0.0'
    port = 10022
    # noinspection PyUnusedLocal
    with SSHTunnelForwarder(
            ("MONGO_SERVER_IP", 22),
            ssh_username="mongo_server_username",
            ssh_pkey="/home/USER/.ssh/KEYFILE",
            remote_bind_address=("localhost", 27017),
            local_bind_address=(local_address, port)
    ) as tunnel:
        sleep(1)

        with pymongo.MongoClient(local_address, port=port) as client:
            # code starts here
            db = client['processing']
            filedb = client['files']
            message_collection = db['needs_processing']
            message_cursor = message_collection.find({})

            for message in message_cursor:
                lab_number = message['lab']
                tars = gridfs.GridFS(filedb, collection='lab'+lab_number)
                # print("working with", message['filename'])
                if (tars.find({"_id": message['filename']}).count()) > 0:
                    continue
                attachment = GetAttachments(service, 'me', message['_id'])
                if len(attachment) is not 1:
                    print("Wrong number of attatchments")
                    continue

                attachment = attachment[0]

                try:
                    filename_ = message['filename'].replace('labA', 'laba').replace('labB', 'labb')
                    tars.put(attachment, _id=filename_)
                    print("inserted", filename_)
                except FileExists:
                    pass


if __name__ == '__main__':
    main()
