FROM python:3.5

WORKDIR /usr/src/app

# install requirements
COPY requirements.txt .
RUN pip install uwsgi && pip install -r requirements.txt

# install module
COPY . .
RUN pip install -e . 

EXPOSE 5000/tcp

CMD [ "flask", "run", "--host=0.0.0.0" ]
