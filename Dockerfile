FROM node:12 AS static
RUN mkdir /code
WORKDIR /code
COPY . /code/
RUN npm i
RUN node_modules/gulp/bin/gulp.js build

FROM python:3.8
ENV PYTHONUNBUFFERED 1
WORKDIR /code
RUN mkdir log
COPY requirements/requirements-prod-aws.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY --from=static /code/analytics ./analytics
COPY --from=static /code/custom-settings ./custom-settings
COPY --from=static /code/dalite ./dalite
COPY --from=static /code/locale ./locale
COPY --from=static /code/peerinst ./peerinst
COPY --from=static /code/quality ./quality
COPY --from=static /code/reputation ./reputation
COPY --from=static /code/static/CACHE ./static/CACHE
COPY --from=static /code/templates ./templates
COPY --from=static /code/tos ./tos
COPY --from=static /code/manage.py .
RUN python3 manage.py collectstatic --clear --noinput
RUN python3 manage.py compress
