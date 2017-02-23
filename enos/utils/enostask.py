# -*- coding: utf-8 -*-
from functools import wraps

import os
import yaml
import logging

def make_env(working_dir=None):
    """Loads the env from `working_dir` if not `None` or makes a new one.

    An Enos environment handles all specific variables of an
    experiment. This function either generates a new environment or
    loads a previous one. If the value of `working_dir` is `None`, then
    this function makes a new environment and return it. If the value
    is a directory path that contains an Enos environment, then this function
    loads and returns it.

    In case of a directory path, this function also rereads the
    configuration file (the reservation.yaml) and reloads it. This
    lets the user update his configuration between each phase.

    """
    env = {
        'config':      {},  # The config
        'resultdir':   '',  # Path to the result directory
        'config_file': '',  # The initial config file
        'nodes':       {},  # Roles with nodes
        'phase':       '',  # Last phase that have been run
        'user':        ''   # User id for this job
    }

    # A new environment is returned if the `env` file does not exist
    if working_dir:
        env_path = os.path.join(working_dir, 'env')

        if os.path.isfile(env_path):
            with open(env_path, 'r') as f:
                env.update(yaml.load(f))
                logging.debug("Loaded environment %s", env_path)

    # Resets the configuration of the environment
    if os.path.isfile(env['config_file']):
        with open(env['config_file'], 'r') as f:
            env['config'].update(yaml.load(f))
            logging.debug("Reloaded config %s", env['config'])

    return env


def save_env(env):
    env_path = os.path.join(env['resultdir'], 'env')

    if os.path.isdir(env['resultdir']):
        with open(env_path, 'w') as f:
            yaml.dump(env, f)


def enostask(doc):
    """Decorator for a Enos Task."""
    def decorator(fn):
        fn.__doc__ = doc

        @wraps(fn)
        def decorated(*args, **kwargs):
            if '--provider' in kwargs:
                provider_name = kwargs['--provider']
                package_name = '.'.join([
                    'enos.provider',
                    provider_name.lower()])
                class_name = provider_name.capitalize()
                module = __import__(package_name, fromlist=[class_name])
                klass = getattr(module, class_name)
                kwargs['provider'] = klass()

            # Loads the environment & set the config
            env = load_env()
            kwargs['env'] = env

            # Proceeds with the function execution
            fn(*args, **kwargs)

            # Save the environment
            save_env(env)

        return decorated
    return decorator
