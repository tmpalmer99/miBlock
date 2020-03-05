FROM ubuntu

RUN apt-get update -y
RUN apt-get install -y python3
RUN apt-get install -y python3-pip

COPY ./requirements.txt /var/www/requirements.txt

RUN mkdir -p /app/miBlock

COPY . /app/miBlock

RUN pip3 install -r /var/www/requirements.txt

WORKDIR /app

ENV FLASK_APP="/app/miBlock/blockchain/REST/node.py"
ENV FLASK_ENV=development
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

CMD ["flask", "run", "--host", "0.0.0.0"]
