import os

from .configutils import _update_config_globals, build_ampq_uri, build_mongo_uri

# ENVIRONMENT SETUP ############################################################

# Application environment, such as dev, staging, production / prod, etc.
# Defaults to 'local'
APP_ENV = os.getenv("APP_ENV", "local")

# Determine whether config/overrides/gsm.yaml should be loaded
# Defaults to True for non-local environments
APP_CONFIG_LOAD_GSM = os.getenv("APP_CONFIG_LOAD_GSM")
if APP_CONFIG_LOAD_GSM is None:
    APP_CONFIG_LOAD_GSM = APP_ENV != "local"
else:
    APP_CONFIG_LOAD_GSM = APP_CONFIG_LOAD_GSM.lower() in ["1", "yes", "yo", "true"]


# EVENTS CONSUMER ##############################################################

EVENTS_APPNAME: str = "local"
EVENTS_AMQP_HOST: str = "localhost"
EVENTS_AMQP_PORT: str = "5672"
EVENTS_AMQP_VHOST: str = "local-application-events"
EVENTS_AMQP_USER: str = "guest"
EVENTS_AMQP_PASSWORD: str = "guest"


# CELERY APP ###################################################################

CELERY_AMQP_HOST: str = "localhost"
CELERY_AMQP_PORT: str = "5672"
CELERY_AMQP_VHOST: str = "local-pc"
CELERY_AMQP_USER: str = "guest"
CELERY_AMQP_PASSWORD: str = "guest"

CELERY_MONGO_HOST: str = "localhost"
CELERY_MONGO_PORT: str = "27017"
CELERY_MONGO_DB: str = "localHome"
CELERY_MONGO_USER: str = ""
CELERY_MONGO_PASSWORD: str = ""


# FLOWER DASHBOARD #############################################################

FLOWER_USER: str = "dev"
FLOWER_PASSWORD: str = "tataace11"
FLOWER_DB_PATH: str = "/volumes/persisted/flowerdb"


# REDIS ########################################################################
REDIS_SET_SENTINEL: str = "False"
REDIS_SENTINEL_NAME: str = 'mymaster'
REDIS_HOST: str = "localhost"
REDIS_PORT: str = "6379"
REDIS_PASSWORD: str = ""
REDIS_SENTINEL_PORT: str = ""
REDIS_SENTINELS: str = ""
REDIS_SENTINEL_PASSWORD: str = ""
REDIX_PREFIX_KEY = 'pay_'
REDIS_DB_NUMBER: int = 0


# MISCELLANEOUS ################################################################

ByPassPaths = ["xyz", "/healthcheck", "/cachehealthcheck", "/changebypass"]
PATHS_TO_IGNORE_FOR_TRACING = "healthcheck,cachehealthcheck"
DEFAULT_PAYMENT_PRECISION = 2
DISTANCE_OFFSET = 1.5
TIME_OFFSET = 30
TIME_MULTIPLIER = 1.2
FARE_MULTIPLIER_VARIABLE = 1.1


# OVERRIDES ####################################################################

# Update module level values with overrides specified in the
# config/overrides/*.yaml files.
_update_config_globals(globals(), APP_ENV, APP_CONFIG_LOAD_GSM)

# NOTE: DO NOT ADD NEW KEYS BEYOND THIS LINE
# New configuration keys should be added in the appropriate section (creating a
# new section if required), and should be added ABOVE the 'OVERRIDES' section
# so that the configuration is properly overridden based on environment.
