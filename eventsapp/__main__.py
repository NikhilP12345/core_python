import config as Config
from core.helpers.cache_helper import CacheHelper
from eventsapp import app

from .sample_handler import handle_sample_event, handle_sample_event_2

if __name__ == "__main__":
    CacheHelper.init(
        Config.REDIS_SET_SENTINEL,
        Config.REDIS_DB_NUMBER,
        Config.REDIX_PREFIX_KEY,
        Config.REDIS_SENTINEL_NAME,
        Config.REDIS_HOST,
        Config.REDIS_PORT,
        Config.REDIS_PASSWORD,
        Config.REDIS_SENTINEL_PORT,
        Config.REDIS_SENTINELS,
        Config.REDIS_SENTINEL_PASSWORD,
    )
    app.run_consumer()
