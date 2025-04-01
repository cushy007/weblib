"""
https://peps.python.org/pep-3333/#original-rationale-and-goals-from-pep-333
https://modwsgi.readthedocs.io/en/master/user-guides/configuration-guidelines.html

"""

# https://modwsgi.readthedocs.io/en/master/user-guides/application-issues.html#user-home-environment-variable
import os, pwd
os.environ["HOME"] = pwd.getpwuid(os.getuid()).pw_dir

##### Uncomment this if Apache can't set it up with /etc/apache2/envvars
#import locale
#locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

import sys
sys.path.insert(0, "%(server_root)s/%(app_name)s/")

from weblib.server import create_app
application, _ = create_app()
