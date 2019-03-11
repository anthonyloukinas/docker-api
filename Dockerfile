# docker run -p 5000:5000 -v /var/run/docker.sock:/var/run/docker.sock aloukinas/docker-api:latest
#
# When running this container you will need to pass through the docker.sock
#
#

FROM python:3

# maintainer
LABEL maintainer = "Anthony Loukinas <anthony.loukinas@redhat.com>"

WORKDIR /app

RUN git clone https://github.com/anthonyloukinas/docker-api.git &&\
    cd /app/docker-api &&\
    pip install -r requirements.txt &&\
    export FLASK_APP=/app/docker-api/client.py

ENTRYPOINT [ "python" ]
CMD [ "/app/docker-api/client.py" ]