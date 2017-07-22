#!/home/TA_NET_ID/.virtualenvs/grading/bin/python

import pull_from_gmail
import get_attatchments
import process_metadata
import consolidate_files

pull_from_gmail.main()
process_metadata.main()
get_attatchments.main()
consolidate_files.main()
