token = "rho sucks at using filters"


try:
    from local_settings import *  # NOQA
except ImportError:
    print("No local_settings.py file")
    print("Get your own token!")
