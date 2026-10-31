"""Run shared choreography through the SDK while respecting desktop Stop."""
import math

from .motions import LABELS, ROUTINES, validate_motion


def run_sequence(mini, stop_event, routine, pose_factory=None, music=True):
    steps = ROUTINES[routine]
    validate_motion(steps)
    if stop_event.is_set():
        return False
    if pose_factory is None:
        from reachy_mini.utils import create_head_pose
        pose_factory = create_head_pose
    if routine == 'auburn' and music:
        from .music import SDKMusicPlayer, perform_auburn
        player = SDKMusicPlayer(mini.media)
        mini.enable_motors()

        def move(step):
            mini.goto_target(
                head=pose_factory(
                    pitch=step.get('pitch', 0), roll=step.get('roll', 0),
                    yaw=step.get('yaw', 0), z=step.get('z_mm', 0), degrees=True, mm=True,
                ),
                antennas=[math.radians(angle) for angle in step['antennas']],
                body_yaw=0, duration=step['duration'],
            )

        return perform_auburn(move, stop_event, player)
    # SDK 1.13 safely pins present targets before enabling torque.
    mini.enable_motors()
    print(LABELS[routine] + ' started.', flush=True)
    moved = False
    completed = False
    try:
        for step in steps:
            if stop_event.is_set():
                break
            print(step['name'], flush=True)
            moved = True
            mini.goto_target(
                head=pose_factory(
                    pitch=step.get('pitch', 0), roll=step.get('roll', 0),
                    yaw=step.get('yaw', 0), z=step.get('z_mm', 0),
                    degrees=True, mm=True,
                ),
                antennas=[math.radians(angle) for angle in step['antennas']],
                body_yaw=0, duration=step['duration'],
            )
            if stop_event.wait(0.15):
                break
        else:
            completed = True
    finally:
        if moved and not completed:
            # Hold a supported neutral pose on Stop. Never drop torque abruptly.
            mini.goto_target(
                head=pose_factory(degrees=True, mm=True),
                antennas=[math.radians(-10), math.radians(10)],
                body_yaw=0, duration=2.0,
            )
    print(LABELS[routine] + (' complete.' if completed else ' stopped.'), flush=True)
    return completed
