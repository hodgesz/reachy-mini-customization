"""Shared choreography: angles in degrees, height offsets in mm, time in seconds."""

HELLO = [
    dict(name='Settle at neutral', pitch=0, antennas=[-10, 10], duration=2.5),
    dict(name='Hello nod', pitch=7, antennas=[-18, 18], duration=1.0),
    dict(name='Look up', pitch=-4, antennas=[-8, 8], duration=1.0),
    dict(name='Wiggle right', pitch=0, antennas=[-24, 8], duration=0.8),
    dict(name='Wiggle left', pitch=0, antennas=[-8, 24], duration=0.8),
    dict(name='Wiggle right again', pitch=0, antennas=[-24, 8], duration=0.8),
    dict(name='Wiggle left again', pitch=0, antennas=[-8, 24], duration=0.8),
    dict(name='Return to neutral', pitch=0, antennas=[-10, 10], duration=1.2),
]

AUBURN = [
    dict(name='Get ready', pitch=0, antennas=[-10, 10], duration=2.5),
    dict(name='Check the left stands', pitch=-3, roll=-5, yaw=12, antennas=[-28, 12], duration=1.0),
    dict(name='Check the right stands', pitch=-3, roll=5, yaw=-12, antennas=[-12, 28], duration=1.2),
    dict(name='Touchdown! Proud head lift', pitch=-7, z_mm=5, antennas=[-8, 8], duration=1.0),
    dict(name='War — sway left', roll=-7, yaw=8, z_mm=2, antennas=[-30, 10], duration=0.8),
    dict(name='Eagle — sway right', roll=7, yaw=-8, z_mm=5, antennas=[-10, 30], duration=0.8),
    dict(name='Cheer left', roll=-7, yaw=8, z_mm=2, antennas=[-30, 10], duration=0.8),
    dict(name='Cheer right', roll=7, yaw=-8, z_mm=5, antennas=[-10, 30], duration=0.8),
    dict(name='Victory bob down', pitch=6, z_mm=0, antennas=[-22, 22], duration=0.8),
    dict(name='Victory bob up', pitch=-6, z_mm=5, antennas=[-8, 8], duration=0.8),
    dict(name='One more victory bob', pitch=6, z_mm=0, antennas=[-22, 22], duration=0.8),
    dict(name='War Eagle finale', pitch=-7, z_mm=5, antennas=[-8, 8], duration=1.0),
    dict(name='Return to neutral', pitch=0, antennas=[-10, 10], duration=1.5),
]

ROUTINES = {"hello": HELLO, "auburn": AUBURN}
LABELS = {"hello": "Hello", "auburn": "Auburn Celebration"}

def validate_motion(steps):
    if not steps:
        raise ValueError('A routine must have at least one pose.')
    for step in steps:
        if any(abs(step.get(axis, 0)) > 15 for axis in ('pitch', 'roll', 'yaw')):
            raise ValueError('Keep head angles within 15 degrees.')
        if not -5 <= step.get('z_mm', 0) <= 8:
            raise ValueError('Keep head height offsets between -5 and 8 mm.')
        if len(step['antennas']) != 2 or any(abs(a) > 40 for a in step['antennas']):
            raise ValueError('Keep antenna angles within 40 degrees.')
        if not 0.7 <= step['duration'] <= 5:
            raise ValueError('Use motion durations between 0.7 and 5 seconds.')
