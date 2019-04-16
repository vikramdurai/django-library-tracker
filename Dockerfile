 FROM python:3
 ENV PYTHONUNBUFFERED 1
 RUN mkdir /code
 RUN apt-get update && apt-get install -y netcat
 WORKDIR /code
 ADD requirements.txt /code/
 RUN pip install -r requirements.txt
 ADD . /code/
 ENTRYPOINT ["/code/entrypoint.sh"]