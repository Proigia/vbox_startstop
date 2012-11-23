vbox_startstop
==============

This script can be used on virtualbox host machines, to stop all running machines (while saving state) and start all previously stopped machines. It is tipically used as a machine startup script.

For info on running the script, start it with the -h or --help option.

For linux users: if you create a symlink (or copy) of the script for your distro in the init dir, to the /etc/init.d/vbox_startstop, you can make sure the script is called on system boot/shutdown.
To make it be called on startup/shutdown issue "sudo update-rc.d vbox_startstop defaults" after putting the script in place.

Make sure you edit the script accoring to your setup. These are the configuration parameters.
VBOX_USERS : This should contain all users (one or more) as which vm's are running. It is possible to start/stop machines from one or several users, by modifying the this parameter. It should be a space separated list.
EXECUTABLE : The EXECUTABLE option should contain the path to the vbox_startstop.py script.
