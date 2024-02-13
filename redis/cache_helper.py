"""Cache-helper module for cache operation
"""
import os
import logging
from redis import sentinel, Redis, RedisError
import json
import logging
import os

from redis import Redis, RedisError, sentinel


class CacheHelper:
    """Helper class for cache operations"""

    redis_client = None
    redis_prefix_key = None

    @staticmethod
    def init(
        set_sentinel=False,
        db=0,
        redis_prefix_key=None,
        sentinel_name=None,
        redis_host=None,
        redis_port=None,
        redis_pass=None,
        redis_sentinel_port=None,
        redis_sentinels=None,
        redis_sentinel_pass=None,
    ):
        """init method for connecting to redis
            :param set_sentinel : decides to use direct redis or sentinel
            :type set_sentinel: boolean
            :param db: redis db number to be used in range of [0 - 15]
            :type db: number
        """
        try:
            # since environment variable sends as string, handling all cases
            CacheHelper.redis_prefix_key = redis_prefix_key
            if set_sentinel in ['True', True]:
                hosts = []
                port = redis_sentinel_port or os.environ.get('REDIS_SENTINEL_PORT', 26379)
                sentinalIps = json.loads(redis_sentinels) if redis_sentinels is not None else json.loads(os.environ.get('REDIS_SENTINELS'))

                logging.info(f'sentinel port: {port}')
                logging.info(f'sentinalIps : {sentinalIps}')
                
                for i in sentinalIps:
                    hosts.append((i, port))

                if not len(hosts):
                    raise Exception("Invalid sentinal hosts")

                CacheHelper.sentinel = sentinel.Sentinel(hosts)
                CacheHelper.redis_client = CacheHelper.sentinel.master_for(
                    sentinel_name,
                    db=db,
                    password=redis_sentinel_pass or os.environ.get('REDIS_SENTINEL_PASS', ''),
                )
            else:
                CacheHelper.redis_client = Redis(
                    host=redis_host or os.environ.get("REDISHOST", "localhost"),
                    port=redis_port or os.environ.get("REDISPORT", "6379"),
                    db=db,
                    password=redis_pass or os.environ.get('REDISPASS', ''),
                    health_check_interval=30,
                    
                )

            logging.info("Redis connected")
        except Exception as e:
            logging.error("Redis not connected : {}".format(e))

    @staticmethod
    def add(key=None, value=None, expiry=None):
        """Add new key into redis

        :param key: key name, defaults to None
        :type key: str, optional
        :param value: value corresponding to key, defaults to None
        :type value: str, optional
        :param expiry: expiry time in seconds, defaults to None
        :type expiry: int, optional
        """
        client = CacheHelper.redis_client
        if key:
            prefixed_key = CacheHelper.add_prefix_to_key(key)
            if CacheHelper.check(key):
                CacheHelper.update(key, value, expiry)
            else:
                if expiry:
                    client.setex(prefixed_key, expiry, value)
                else:
                    client.set(prefixed_key, value)

    @staticmethod
    def update(key=None, value=None, expiry=None):
        """Update the value of a key with new-value

        :param key: name of the key, defaults to None
        :type key: str, optional
        :param value: value to be updated with, defaults to None
        :type value: str, optional
        :param expiry: expiry time, defaults to None
        :type expiry: int, optional
        :return: True if updated else False
        :rtype: bool
        """
        return_value = False
        if key:
            prefixed_key = CacheHelper.add_prefix_to_key(key)
            client = CacheHelper.redis_client
            retry_count = 0
            while retry_count < 3:
                try:
                    val = client.get(prefixed_key)
                    if val is not None:
                        if expiry:
                            if value is None:
                                value = val
                            client.setex(prefixed_key, expiry, value)
                        else:
                            client.set(prefixed_key, value)
                        return_value = True
                    break
                except RedisError as e:
                    retry_count += 1
                    logging.error(e)
                    logging.warning(
                        "RedisError #%d: %s; retrying" + str(retry_count) + key
                    )
        return return_value

    @staticmethod
    def check(key=None):
        """Check If key exist in the redis

        :param key: name of the redis key, defaults to None
        :type key: str, optional
        :return: True if exists else False
        :rtype: bool
        """
        if not key:
            return None
        prefixed_key = CacheHelper.add_prefix_to_key(key)
        client = CacheHelper.redis_client
        return client.exists(prefixed_key)

    @staticmethod
    def get(key=None):
        """Get the value of given redis key

        :param key: name of the redis key, defaults to None
        :type key: str, optional
        :return: value of the key If exists else None
        :rtype: str
        """
        if key:
            prefixed_key = CacheHelper.add_prefix_to_key(key)
            client = CacheHelper.redis_client
            data = client.get(prefixed_key)
            if data is not None:
                return data.decode()
        return None

    @staticmethod
    def delete(key=None):
        """Delete the redis key

        :param key: name of the key to be deleted, defaults to None
        :type key: str, optional
        """
        if key:
            prefixed_key = CacheHelper.add_prefix_to_key(key)
            client = CacheHelper.redis_client
            client.delete(prefixed_key)
    
    @staticmethod
    def multi_delete(*keys)->int:
        """Delete all the redis keys passed

        :param keys: keys to be deleted
        :type key: str, int, float

        Example:
        multi_delete(key1, key2)
        """
        if len(keys)==0:
            logging.warning('No keys passed to delete from cache')
            return 0
        prefixed_keys = list(map(CacheHelper.add_prefix_to_key, keys))
        client = CacheHelper.redis_client
        return client.delete(*prefixed_keys)

    @staticmethod
    def flush_all():
        """Delete all the key of the redis db"""
        CacheHelper.redis_client.flushall()

    @staticmethod
    def setLock(key, expiry):
        """Get Lock on the Key
        :param key: key name, defaults to None
        :type key: str
        :param expiry: expiry time in seconds, defaults to None
        :type expiry: int
        """
        client = CacheHelper.redis_client
        try:
            if key and expiry:
                prefixed_key = CacheHelper.add_prefix_to_key(key)
                client.incr(prefixed_key)
                client.expire(prefixed_key, expiry)
                val = client.get(prefixed_key)
                if not val:
                    raise Exception(
                        {
                            "code": 500,
                            "type": "lock",
                            "message": "Failed to get lock",
                        }
                    )
                val = int(chr(int.from_bytes(val, "big")))
                if val == 1:
                    return key
                else:
                    raise Exception(
                        {
                            "code": 500,
                            "type": "lock",
                            "message": "Failed to get lock",
                        }
                    )

            else:
                raise Exception(
                    {
                        "code": 500,
                        "type": "lock",
                        "message": "Failed to get lock",
                    }
                )

        except Exception as e:
            raise Exception(
                {
                    "code": 500,
                    "type": "lock",
                    "message": "Failed to get lock -> " + str(e),
                }
            )

    @staticmethod
    def add_prefix_to_key(key):
        """ add Prefix in front of key
        """
        if not key or not CacheHelper.redis_prefix_key:
            return key
        return CacheHelper.redis_prefix_key + key