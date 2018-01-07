#!/usr/bin/env python

from bcc.remote import shell

s = shell.ShellRemote()
print s.send_command('testxx')
