#############################################################################
# Project         : Linux-Mandrake
# Module          : rpmlint
# File            : PostCheck.py
# Version         : $Id$
# Author          : Frederic Lepied
# Created On      : Wed Jul  5 13:30:17 2000
# Purpose         : Check post/pre scripts
#############################################################################

from Filter import *
import AbstractCheck
import rpm
import re
import os
import commands

DEFAULT_VALID_SHELLS=('/bin/sh',
                      '/bin/bash',
                      '/sbin/sash',
                      '/usr/bin/perl',
                      )

extract_dir=Config.getOption('ExtractDir', '/tmp')
valid_shells=Config.getOption('ValidShells', DEFAULT_VALID_SHELLS)

braces_regex=re.compile("^[^#]*%", re.MULTILINE)
bracket_regex=re.compile("^[^#]*if.*[^ \]]\]", re.MULTILINE)
home_regex=re.compile('[^a-zA-Z]+~|\$HOME', re.MULTILINE)
dangerous_command_regex=re.compile("(^|\s|;)(cp|mv|ln|tar|rpm|chmod|chown|rm|cpio)\s", re.MULTILINE)

def incorrect_shell_script(shellscript):
    tmpfile = "%s/.bash-script.%d" % (extract_dir, os.getpid())
    if not shellscript:
        return 0
    file=open(tmpfile, 'w')
    file.write(shellscript)
    file.close()
    ret=commands.getstatusoutput("/bin/bash -n %s" % tmpfile)
    os.remove(tmpfile)
    return ret[0]

def incorrect_perl_script(perlscript):
    tmpfile = "%s/.perl-script.%d" % (extract_dir, os.getpid())
    if not perlscript:
        return 0
    file=open(tmpfile, 'w')
    file.write(perlscript)
    file.close()
    ret=commands.getstatusoutput("/usr/bin/perl -wc %s" % tmpfile)
    os.remove(tmpfile)
    return ret[0]

class PostCheck(AbstractCheck.AbstractCheck):
    
    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "PostCheck")

    def check(self, pkg, verbose):
	# Check only binary package
	if pkg.isSource():
	    return

        for tag in ((rpm.RPMTAG_PREIN, rpm.RPMTAG_PREINPROG, "%pre"),
                    (rpm.RPMTAG_POSTIN, rpm.RPMTAG_POSTINPROG, "%post"),
                    (rpm.RPMTAG_PREUN, rpm.RPMTAG_PREUNPROG, "%preun"),
                    (rpm.RPMTAG_POSTUN, rpm.RPMTAG_POSTUNPROG, "%postun")):
            script = pkg[tag[0]]
            prog = pkg[tag[1]]
            if script:
                if prog:
                    if not prog in valid_shells:
                        printError(pkg, "invalid-shell-in-" + tag[2], prog)
                if prog == "/bin/sh" or prog == "/bin/bash" or prog == "/usr/bin/perl":
                    if braces_regex.search(script):
                        printWarning(pkg, "percent-in-" + tag[2])
                    if bracket_regex.search(script):
                        printWarning(pkg, "spurious-bracket-in-" + tag[2])
                    res=dangerous_command_regex.search(script)
                    if res:
                        printWarning(pkg, "dangerous-command-in-" + tag[2], res.group(2))
                        
                if prog == "/bin/sh" or prog == "/bin/bash":
                    if incorrect_shell_script(script):
                        printError(pkg, "shell-syntax-error-in-" + tag[2])
                    if home_regex.search(script):
                        printError(pkg, "use-of-home-in-" + tag[2])

                if prog == "/usr/bin/perl":
                    if incorrect_perl_script(script):
                        printError(pkg, "perl-syntax-error-in-" + tag[2])
            else:
                if prog in valid_shells:
                    printWarning(pkg, "empty-" + tag[2])
                    
# Create an object to enable the auto registration of the test
check=PostCheck()

# PostCheck.py ends here
