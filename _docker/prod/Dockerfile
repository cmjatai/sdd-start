FROM leandrojatai/building_foundation:0002

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

ENV ROOT_HOME=/var/project
ENV HOME=${ROOT_HOME}/backend

RUN mkdir -p ${HOME}/run
RUN mkdir -p ${HOME}/logs/celery
RUN mkdir -p ${ROOT_HOME}/backend_data
RUN mkdir -p ${ROOT_HOME}/backend_media

WORKDIR ${HOME}

COPY manage.py ${HOME}

COPY py* ${HOME}
RUN poetry install --without dev,test,docs

#COPY package-lock.json ${HOME}
COPY package.json   ${HOME}
COPY vite.config.js ${HOME}

ADD _frontend   ${HOME}/_frontend
RUN npm install
RUN npm run build

ADD solr        ${HOME}/solr
ADD drfautoapi  ${HOME}/drfautoapi
ADD backend     ${HOME}/backend
ADD _templates  ${HOME}/_templates
ADD _docker     ${HOME}/_docker

RUN python3 manage.py collectstatic --noinput --clear --settings=backend.settings.fake --no-default-ignore

RUN rm -rf ${HOME}/db.sqlite3

COPY _docker/prod/nginx/backend_docker.conf /etc/nginx/conf.d/.
COPY _docker/prod/nginx/nginx_docker.conf /etc/nginx/nginx.conf

COPY _docker/prod/start.sh ${HOME}
COPY _docker/prod/wait-for-pg.sh ${HOME}
COPY _docker/prod/wait-for-solr.sh ${HOME}
COPY _docker/prod/start_gunicorn.sh ${HOME}
COPY _docker/prod/start_daphne.sh ${HOME}
COPY _docker/prod/solr_cli.py ${HOME}
COPY _docker/prod/genkey.py ${HOME}

RUN chmod +x ${HOME}/start.sh && \
    chmod +x ${HOME}/start_gunicorn.sh && \
    chmod +x ${HOME}/start_daphne.sh && \
    chmod +x ${HOME}/wait-for-solr.sh && \
    chmod +x ${HOME}/wait-for-pg.sh

# Debian não possui usuário 'nginx' necessário para o Debian
RUN useradd -r -u 1002 --no-create-home -g root nginx

USER nginx

ENV DEBIAN_FRONTEND=teletype

EXPOSE 80/tcp

VOLUME ["${ROOT_HOME}/backend_data", "${ROOT_HOME}/backend_media", "${HOME}/logs"]

CMD ["/var/project/backend/start.sh"]
