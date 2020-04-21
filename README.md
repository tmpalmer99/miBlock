# miBlock - User Manual
## Prerequisites
### Installing Docker
**1.** Use apt command to install the docker.io package:

```
$ sudo apt install docker.io
```

**2.** Start docker and enable it to start after the system reboot:
```
$ sudo systemctl enable --now docker
```

**3.** In order to use a virtual environment, make sure docker runs without sudo:
```
$ sudo groupadd docker
$ sudo gpasswd -a $USER docker
$ newgrp docker
```
**4.** Run docker test using the hello-world container:
```
$ docker run hello-world

Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 https://hub.docker.com/

For more examples and ideas, visit:
 https://docs.docker.com/get-started/
```
### Installing pip3 and virtualenv
```
$ sudo apt update
$ sudo apt install python3-pip
$ sudo pip3 install virtualenv
```
---
## Environment Setup for miBlock
### Clone the repository
**1.** Change into a directory where you want to place the cloned repository and execute the following:
```
$ git clone https://github.com/tmpalmer99/miBlock.git miBlock
```
**2.** Change directory into miBlock and create a virtual environment
```
$ cd miBlock/
$ python3 -m venv miBlockVenv
```
**3.** Install all necessary modules for the client
```
$ source miBlockVenv/bin/activate
$ pip3 install prettytable
$ pip3 install requests
```
# Running miBlock
**1.** With the virtual environment still activated, from the root directory of the miBlock repository a network can be created by executing the following script (the first time this is executed it will take a few minutes to produce the docker image):
```
$ ./create_network.sh n    <- n here is the number of nodes we want to have in the network
```
If this command fails with permission denied, run the following commands again with venv activated
```
$ sudo groupadd docker
$ sudo gpasswd -a $USER docker
$ newgrp docker
```

![Create Network](https://github.com/tmpalmer99/miBlock/blob/master/demo/images/createscript.png)

**2.** If the environment has been successfully setup then the client should now be running and all commands available to the user will be outlined.

# Using miBlock
Upon running the demonstration client succesfully, the user has the ability to login to a node, register a single node or all nodes, and list available nodes:

![Login](https://github.com/tmpalmer99/miBlock/blob/master/demo/images/login.png)

Once a user logs in to a node to send requests on their behalf, they are faced with the following available commands.

![Commands](https://github.com/tmpalmer99/miBlock/blob/master/demo/images/client_commands.png)

## Mining Procedure

The steps necessary in the mining procedure are:
1. login in to a node
2. execute the 'record' command
3. (optional) execute the 'show-examples' command to list available records to add
4. add any number of records using the 'add' command
5. once records are added return to the command menu
6. execute the 'mine' command
7. (optional) print the blockchain using 'chain'

![Mining](https://github.com/tmpalmer99/miBlock/blob/master/demo/images/mining.png)

## Using Chord

Given that a user has logged into a node, the 'chord' command can be executed to show the menu for all chord related commands. An example is show below of a look-up operation for key 500.


![Chord](https://github.com/tmpalmer99/miBlock/blob/master/demo/images/chord_lookup.png)
