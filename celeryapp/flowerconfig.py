import config

persistent = True
db = config.FLOWER_DB_PATH

basic_auth = [f"{config.FLOWER_USER}:{config.FLOWER_PASSWORD}"]
