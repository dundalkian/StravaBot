FROM alpine:3.8

COPY . /app
WORKDIR /app

RUN apk add --update python3 python-dev py-pip py3-psycopg2 py-lxml git 

RUN pip3 install --upgrade pip

# Removes psycopg pip install which was installed via apk.
RUN sed '1d' requirements.txt > docker_reqs.txt

RUN pip3 install -r docker_reqs.txt

RUN git pull && git checkout StravaBot-8_LS

CMD ["python3", "bot.py"]
