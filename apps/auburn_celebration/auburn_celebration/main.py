"""Auburn Celebration: play once from Reachy Mini Control."""
from reachy_customizations.sdk_app import SequenceApp, launch


class AuburnCelebration(SequenceApp):
    custom_app_url = None
    routine = 'auburn'


if __name__ == '__main__':
    launch(AuburnCelebration)
