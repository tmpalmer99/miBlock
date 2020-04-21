# miBlock - User Manual
## Prerequisites
### Installing Docker
**1.** Update the apt package index and install packages to allow apt to use a repository over HTTPS:

<div>

```
$ sudo apt-get update
$ sudo apt-get install apt-transport-https ca-certificates curl gnupg-agent software-properties-common
```

 </div>

**2.** Add Docker’s official GPG key:

```
$ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
```

**3.** Verify that you now have the key with the fingerprint 9DC8 5822 9FC7 DD38 854A  E2D8 8D81 803C 0EBF CD88, by searching for the last 8 characters of the fingerprint.

```
 $ sudo apt-key fingerprint 0EBFCD88

Output:
-------
pub   rsa4096 2017-02-22 [SCEA]
      9DC8 5822 9FC7 DD38 854A  E2D8 8D81 803C 0EBF CD88
uid           [ unknown] Docker Release (CE deb) <docker@docker.com>
sub   rsa4096 2017-02-22 [S]
```
**4.** Use the following command to set up the stable repository.
```
$ sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
```

**5.** Update the apt package index, and install the latest version of Docker Engine and containerd, or go to the next step to install a specific version:
```
$ sudo apt-get update
$ sudo apt-get install docker-ce docker-ce-cli containerd.io
```

**6.** In order to use a virtual environment, make sure docker runs without sudo
```
$ sudo groupadd docker
$ sudo gpasswd -a $USER docker
$ newgrp docker
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
## Running miBlock
**1.** With the virtual environment still activated, from the root directory of the miBlock repository a network can be created by executing the following script (the first time this execute it will take a few minutes to produce the docker image):
```
$ ./create_network.sh n    <- n here is the number of nodes we want to have in the network
```
**2.** If the environment has been successfully setup then the client should now be running and all available commands are clearly outlined to the user
