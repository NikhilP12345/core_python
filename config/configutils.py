import logging
import os
import time

import yaml
from google.cloud.secretmanager import SecretManagerServiceClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


_SUPPORTED_ANNOTATIONS_FOR_CONVERSION = {str, float, int, bool}


class OverrideEntry:

    __SUPPORTED_VARIANTS__ = ["plain", "gsm"]

    def __init__(self, variant, config, value):
        self.variant = variant
        self.config = config
        self.value = value

        if self.variant not in self.__SUPPORTED_VARIANTS__:
            raise Exception("Unsupported variant found for config override entry")


def build_ampq_uri(host, port, vhost, user, password):
    return f"amqp://{user}:{password}@{host}:{port}/{vhost}"


def build_mongo_uri(host, port, db, user, password):
    auth_component = ""
    if user or password:
        auth_component = f"{user}:{password}@"

    if host == "localhost":
        return f"mongodb://{auth_component}localhost:{port}/{db}"

    return f"mongodb+srv://{auth_component}{host}/{db}"


def _update_config_globals(_globals, env, load_gsm=False):
    """
    WARNING: This function is ONLY meant for the config module, use it
    elsewhere at your own peril.

    This function mutates the config module to override configuration keys
    already defined in the module. This is done using two files:
        - config/overrides/gsm.yaml
        - config/overrides/<env>.yaml

    Values inside <env>.yaml take precedence over values in gsm.yaml. This
    allows one to override the secret value from the repository in certain use
    cases, say while testing in environments that does not have the secrets.
    Note that if gsm.yaml is being loaded, only those keys will be fetched
    from GSM that have not been further overridden by <env>.yaml.

    If the config key has a type annotation class that is a part of
    _SUPPORTED_ANNOTATIONS_FOR_CONVERSION, then that class is used to convert
    the final value to that type. This applies only to overridden values from
    the YAML files; correcting the type of default values in the module that
    may have been incorrectly configured is not attempted. To fix the default
    values, try opening your eyes wider and assign the right types.

    The function raises an Exception when:
        - GSM does not have a secret configured in gsm.yaml
        - YAML files do not exist or are invalid YAMLs
        - YAML files have a config key that is not a part of the config module
        - Type conversion according to the annotation has failed
        - Author of this function has checked in a sneaky little bug

    Args:
        _globals (dict): The globals() object from the config module.
        env (str): Deployment environment such as dev, prod, etc. Corresponding
            config/overrides/<env>.yaml file will be loaded.
        load_gsm (bool, optional): Determine if config/overrides/gsm.yaml
            should be loaded. Defaults to False.
    """
    overrides = {}

    # Load the env-specific YAML file
    with open(f"config/overrides/{env}.yaml") as env_file:
        overrides.update(yaml.safe_load(env_file) or {})

    # Load GSM if enabled
    if load_gsm:
        gsm_start_time = time.time()
        with open("config/overrides/gsm.yaml") as gsm_file:
            gsm_map = yaml.safe_load(gsm_file) or {}

        project = os.getenv("GSM_PROJECT_ID")
        if not project:
            raise Exception("'GSM_PROJECT_ID' environment variable must be set!")

        gsm_client = SecretManagerServiceClient()

        for config_key, gsm_secret_name in gsm_map.items():

            # Ignore GSM config for keys that are already in overrides
            if config_key in overrides:
                continue

            # Fetch from GSM
            secret_version_path = gsm_client.secret_version_path(project, gsm_secret_name, "latest")
            overrides[config_key] = gsm_client.access_secret_version(name=secret_version_path).payload.data.decode()

        gsm_run_time = time.time() - gsm_start_time
        logger.info("Loading secrets from GSM took %.2f seconds", gsm_run_time)

    # Validate overrides
    for config_key in overrides.keys():
        # Ensure unknown keys are not present in overrides
        if config_key not in _globals:
            raise Exception(f"Key <{config_key}> found in overrides but not present in the config module")

        # Type cast as per annotations
        type_class = _globals.get("__annotations__", {}).get(config_key)
        if type_class in _SUPPORTED_ANNOTATIONS_FOR_CONVERSION:
            try:
                overrides[config_key] = type_class(overrides[config_key])
            except Exception:
                logger.exception("Unable to convert override value for key %s to type %s", config_key, type_class)
                raise

    # Finally, update globals
    _globals.update(overrides)
