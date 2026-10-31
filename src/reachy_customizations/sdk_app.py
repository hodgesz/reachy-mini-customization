"""Shared managed-app lifecycle; imported only in Reachy's app environment."""
import signal

from reachy_mini import ReachyMiniApp

from .sdk_runner import run_sequence


class SequenceApp(ReachyMiniApp):
    custom_app_url = None
    request_media_backend = 'no_media'
    routine = 'hello'

    def run(self, reachy_mini, stop_event):
        run_sequence(reachy_mini, stop_event, self.routine)


def launch(app_class):
    app = app_class()
    # App manager sends SIGINT for Stop. Set its event so a short current
    # interpolation finishes and the app can return smoothly to neutral.
    def request_stop(signum, frame):
        app.stop()
    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    app.wrapped_run()
