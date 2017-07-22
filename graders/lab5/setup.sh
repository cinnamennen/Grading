#!/usr/bin/env bash
sh -c 'chmod 0700 test-dir your-dir 2>/dev/null'
sh -c 'chmod -R 0700 test-dir your-dir 2>/dev/null'
rm -rf test-dir your-dir  tarfile
rm -f tmp-090-test-stdout.txt tmp-090-test-stderr.txt
/home/plank/cs360/labs/lab5/Gradescript-Examples/mrd 90 13 7 d 27 your-dir
