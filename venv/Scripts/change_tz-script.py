#!C:\Python27\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'vobject==0.9.3','console_scripts','change_tz'
__requires__ = 'vobject==0.9.3'
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.exit(
        load_entry_point('vobject==0.9.3', 'console_scripts', 'change_tz')()
    )
