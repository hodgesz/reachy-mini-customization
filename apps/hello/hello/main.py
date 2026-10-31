"""Hello: play once from Reachy Mini Control."""
from reachy_customizations.sdk_app import SequenceApp, launch


class Hello(SequenceApp):
    custom_app_url = None
    routine = 'hello'


if __name__ == '__main__':
    launch(Hello)
