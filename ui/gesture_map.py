"""Single source of truth for the CV gesture -> spell mapping.

The recognizer in game.py compares live MediaPipe hand landmarks against the
poses trained in gestures.json. This module reconciles three things that are
currently inconsistent in the legacy code, WITHOUT editing that code:

  * gestures.json trains 8 poses: peace, thumb, palm, no ring, lvibe, gun,
    spiderman, fist.
  * game.py's spell_map wires only 7 of them and leaves "no ring" unused.
  * SPELLS defines 8 spells, but "shadow" and "solarbeam" have NO gesture and
    are only reachable from the keyboard (keys 7 and 8).

Every screen and the camera panel render their gesture guidance from GESTURE_MAP
so the on-screen UI always reflects what the recognizer can actually do. The
legacy positional hints ("Top-Right Hand", "Both Hands Up") are intentionally
replaced with the real single-hand pose names.

Each entry:
    pose:      the key as trained in gestures.json (None => keyboard only)
    spell_id:  the SPELLS key the cast resolves to ("start" == control action)
    key:       the keyboard fallback key
    label:     human pose description shown in the UI
"""

# Gesture-first control scheme (Susnata).
#
# 'pose' MUST be a key trained in gestures.json for the recognizer to fire it.
# Trained poses available today: peace, thumb, palm, no ring, lvibe, gun,
# spiderman, fist.
#
# Some desired gestures (☝️ index-point, 🩰 finger-heart, 👌 OK, 🤌 pinch) have
# NOT been recorded yet, so their 'pose' is None and 'needs_pose' is True: they
# are keyboard-castable now and light up automatically once you record the pose
# into gestures.json under the name given by 'record_as'.
#
# Fields:
#   emoji      display glyph for the gesture
#   gesture    human name of the intended hand gesture
#   spell_id   spell the cast resolves to ("start" == control action)
#   pose       trained gestures.json key, or None if not yet recorded
#   record_as  gestures.json key to record the missing pose under
#   key        keyboard fallback key
#   needs_pose True if a pose still has to be recorded to enable gestures
GESTURE_BINDINGS = [
    {"emoji": "👍", "gesture": "Thumbs Up",      "spell_id": "start",       "pose": "thumb",     "record_as": "thumb",     "key": "SPACE", "needs_pose": False},
    {"emoji": "☝️", "gesture": "Index Point",     "spell_id": "lightning",   "pose": None,        "record_as": "point",     "key": "1",     "needs_pose": True},
    {"emoji": "✌️", "gesture": "Peace Sign",      "spell_id": "ice",         "pose": "peace",     "record_as": "peace",     "key": "2",     "needs_pose": False},
    {"emoji": "🤘", "gesture": "Rock Horns",      "spell_id": "fire",        "pose": "lvibe",     "record_as": "lvibe",     "key": "3",     "needs_pose": False},
    {"emoji": "🩰", "gesture": "Finger Heart",    "spell_id": "heal",        "pose": None,        "record_as": "heart",     "key": "4",     "needs_pose": True},
    {"emoji": "👎", "gesture": "Thumbs Down",    "spell_id": "earthquake",  "pose": "no ring",   "record_as": "no ring",   "key": "5",     "needs_pose": False},
    {"emoji": "🖐️", "gesture": "Open Hand",     "spell_id": "shield",      "pose": "palm",      "record_as": "palm",      "key": "6",     "needs_pose": False},
    {"emoji": "👌", "gesture": "OK Sign",         "spell_id": "blackhole",   "pose": None,        "record_as": "ok",        "key": "7",     "needs_pose": True},
    {"emoji": "🤌", "gesture": "Pinch",           "spell_id": "telekinesis", "pose": None,        "record_as": "pinch",     "key": "8",     "needs_pose": True},
]

# Convenience lookups.
GESTURE_MAP = {b["spell_id"]: b for b in GESTURE_BINDINGS}
POSE_TO_SPELL = {b["pose"]: b["spell_id"] for b in GESTURE_BINDINGS if b["pose"]}


def spell_bindings():
    """Return only the 8 castable spells (excludes the 'start' control action)."""
    return [b for b in GESTURE_BINDINGS if b["spell_id"] != "start"]


def binding_for(spell_id):
    return GESTURE_MAP.get(spell_id)


# Spells that do not require an enemy target to cast (self/AoE spells). Used by
# game.py so the target-required guard in SpellManager.cast can be bypassed.
NO_TARGET_SPELLS = {"shield", "earthquake", "heal", "blackhole"}


def pending_poses():
    """Return bindings whose hand pose still needs recording in gestures.json."""
    return [b for b in GESTURE_BINDINGS if b.get("needs_pose")]
