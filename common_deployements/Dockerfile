FROM gcr.io/google-appengine/python


# SETUP PYTHON ENV #############################################################

# Create a virtualenv for dependencies. This isolates these packages from
# system-level packages.
RUN virtualenv -p python3.7 /env

# Setting these environment variables are the same as running
# source /env/bin/activate.
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH


# SETUP WORKSPACE ##############################################################

WORKDIR /app

# Install dependencies before copying over application code, to benefit from
# docker's caching mechanism
ADD requirements.txt requirements.txt
ADD core/requirements.txt core/requirements.txt
RUN pip install -r requirements.txt

# Add application source code
ADD . .


# SETUP ENVIRONMENT ############################################################

ENV PORT 8080
ENV APP_ENV dev

EXPOSE 8080


# ENTRYPOINT CONFIGURATION #####################################################

# The entrypoint supports multiple execution modes, for example '-m server' to
# start the web server or '-m worker -q celery' to start a celery worker
# listening on the 'celery' queue

ENTRYPOINT ["/bin/bash", "scripts/entrypoint.sh"]
CMD ["-m", "server"]
