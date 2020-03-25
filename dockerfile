FROM ubuntu

RUN apt-get update -y
RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN pip3 install Flask==1.1.1
RUN pip3 install requests==2.23.0

ENV FLASK_APP='/app/miBlock/blockchain/REST/node.py'
ENV FLASK_ENV=development
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN mkdir -p /app/miBlock

COPY . /app/miBlock

WORKDIR /app


CMD ["flask", "run", "--host", "0.0.0.0"]
