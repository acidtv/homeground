FROM python:3.5

WORKDIR /usr/src/app

COPY . .

RUN pip install uwsgi && pip install -e . 

EXPOSE 5000/tcp

CMD [ "flask", "run", "--host=0.0.0.0" ]
