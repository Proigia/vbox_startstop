#!/usr/bin/env python
"""Stop all running virtualbox machines, or start the ones that were previously stopped. For more info, see the usage method (or call 'vbox_startstop.py help')"""

__author__      = "Dolf Andringa"
__copyright__   = "Copyright (c) 2012, Dolf Andringa"

__license__     = "MIT License"
__version__     = "1.0"
__maintainer__  = "Dolf Andringa"
__email__       = "dolfandringa@gmail.com"
__status__      = "Production"

__licensetext__ = """Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE."""

from vboxapi import VirtualBoxManager
import sys, getopt, os, time, traceback

def usage():
    print """
usage: vbox_startstop.py <command> (-h|--help)
Stop (with saving state) all currently running virtualbox virtual machines or start all previously stopped virtual machines.

Arguments:
    -h | --help  :  Show this help
    command      :  stop      : All currently running virtual machines will be stopped while saving the current state.
                                The uuids of the machines will be written to ~/.vbox_startstop/stopped_machines.
                    start     : All machines listed in ~/.vbox_startstop/stopped_machines will be started
                    restart   : The same as calling "vbox_startstop.py stop;vbox_startstop.py start"
                    help      : Show this help
"""

RUNNING_STATES=['LastOnline','FirstOnline','Paused','Running']
DIRNAME=os.path.expanduser('~/.vbox_startstop')


class FileLockedError(Exception):
    pass

def prepare():
    global DIRNAME
    if not os.path.isdir(DIRNAME):
        os.mkdir(DIRNAME)
        open(os.path.join(DIRNAME,'stopped_machines'),'w')
    lockdir()
    mgr=VirtualBoxManager(None,None)
    vbox=mgr.vbox
    session=mgr.mgr.getSessionObject(vbox)
    return mgr,vbox,session

def finish():
    unlockdir()

def lockdir():
    global DIRNAME
    lockfile=os.path.join(DIRNAME,'lock')
    if os.path.exists(lockfile):
        raise FileLockedError('Another process is currently starting or stopping vbox machines, or there is a stale lock file in %s.'%lockfile)
    f=open(lockfile,'w')
    f.close()

def unlockdir():
    global DIRNAME
    lockfile=os.path.join(DIRNAME,'lock')
    os.remove(lockfile)

def get_stopped_machines_file(mode):
    global DIRNAME
    f=open(os.path.join(DIRNAME,'stopped_machines'),mode)
    return f


def stop_machine(m,session,mgr):
    try:
        m.lockMachine(session,mgr.constants.LockType_Shared)
        console=session.console
        progress=console.saveState()
        progress.waitForCompletion(-1)
        session.unlockMachine()
    except Exception:
        print('Failed saving machine state for machine %s. We will continue stopping the other machines.\n\nError: %s.\n\n'%(m.state,traceback.format_exc()))

def stop_all_machines(mgr,vbox,session):
    machine_states=dict([(v,k) for k,v in mgr.constants.all_values('MachineState').items()])
    machines=mgr.getArray(vbox,'machines')
    starting_machines=[m for m in machines if machine_states[m.state]=='Starting']
    running_machines=[m for m in machines if machine_states[m.state] in RUNNING_STATES]
    stopped_machines=[]
    for m in running_machines:
        print('Stopping machine %s'%m.name)
        stop_machine(m,session,mgr)
        stopped_machines.append(m)
    for m in starting_machines:
        i=0
        while machine_states[m.state]=='Starting' and i<=5:
            print('Machine %s is still starting up. Waiting for it to be started.'%m.name)
            time.sleep(10)
            i+=1
        if machine_states[m.state]=='Starting':
            print('Machine %s is still starting up. Giving up waiting on it. We\'ll try to save state, but continue otherwise.'%m.name)
        stop_machine(m,session,mgr)
        stopped_machines.append(m)
    f=get_stopped_machines_file('w')
    for m in stopped_machines:
        f.write("%s\n"%m.id)
    f.close()

def start_stopped_machines(mgr,vbox,session):
    machine_states=dict([(v,k) for k,v in mgr.constants.all_values('MachineState').items()])
    stopped_machines=[vbox.findMachine(l.strip()) for l in get_stopped_machines_file('r').readlines()]
    started_machines=[]
    for m in stopped_machines:
        try:
            print('Starting machine %s'%m.name)
            progress=m.launchVMProcess(session,'headless','')
            progress.waitForCompletion(-1)
            mgr.closeMachineSession(session)
            started_machines.append(m)
        except Exception:
            print('Unable to start machine %s. Continue to start other machines.\n\nError: %s.\n\n'%(m.name,traceback.format_exc()))
    get_stopped_machines_file('w').write("\n".join(list(set([m.id for m in stopped_machines]).difference(set([m.id for m in started_machines])))))


if __name__=='__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o,a in opts:
        if o in ('-h','--help'):
            usage()
            sys.exit()
    if len(args)<>1:
        usage()
        sys.exit(2)
    elif args[0]=='stop':
        mgr,vbox,session=prepare()
        try:
            stop_all_machines(mgr,vbox,session)
        finally:
            finish()
    elif args[0]=='start':
        mgr,vbox,session=prepare()
        try:
            start_stopped_machines(mgr,vbox,session)
        finally:
            finish()
    elif args[0]=='restart':
        mgr,vbox,session=prepare()
        try:
            stop_all_machines(mgr,vbox,session)
            time.sleep(5)
            start_stopped_machines(mgr,vbox,session)
        finally:
            finish()
    elif args[0]=='help':
        usage()
        sys.exit()
    else:
        usage()
        sys.exit(2)
