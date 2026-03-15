import threading
import time
from enum import Enum


class State(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    THINKING = "thinking"
    STREAMING = "streaming"
    RESPONSE = "response"
    ERROR = "error"


STATE_COLORS = {
    State.IDLE:          (90, 90, 90),
    State.LISTENING:     (0, 80, 255),
    State.TRANSCRIBING:  (255, 200, 0),
    State.THINKING:      (255, 200, 0),
    State.STREAMING:     (0, 200, 50),
    State.RESPONSE:      (0, 160, 80),
    State.ERROR:         (255, 0, 0),
}

_TAP_THRESHOLD = 0.4


class ButtonPTT:
    """Tracks push-to-talk button and application state."""

    def __init__(self, board, on_press_cb=None, on_release_cb=None, on_cancel_cb=None,
                 cancel_allowed_cb=None, on_any_press_cb=None, on_abort_listening_cb=None,
                 on_tap_cb=None, is_sleeping_cb=None):
        self._board = board
        self._on_press = on_press_cb
        self._on_release = on_release_cb
        self._on_cancel = on_cancel_cb
        self._on_any_press = on_any_press_cb
        self._on_abort_listening = on_abort_listening_cb
        self._on_tap = on_tap_cb
        self._cancel_allowed = cancel_allowed_cb
        self._is_sleeping = is_sleeping_cb
        self._state = State.IDLE
        self._lock = threading.Lock()
        self._press_time = 0.0
        self._tap_timer = None

        board.on_button_press(self._handle_press)
        board.on_button_release(self._handle_release)

    @property
    def state(self) -> State:
        return self._state

    @state.setter
    def state(self, new_state: State):
        with self._lock:
            self._state = new_state
            self._update_led(new_state)

    def _update_led(self, state: State):
        if state == State.IDLE:
            return
        color = STATE_COLORS.get(state, (40, 40, 40))
        try:
            self._board.set_backlight_color(*color)
        except AttributeError:
            pass

    def _handle_press(self):
        self._press_time = time.monotonic()

        # Check if display is sleeping BEFORE waking it
        was_sleeping = self._is_sleeping() if self._is_sleeping else False

        # Always wake display on any press
        if self._on_any_press:
            self._on_any_press()

        # If we just woke the display, don't do anything else
        if was_sleeping:
            return

        # RESPONSE state: wait to see if it's a tap or hold
        if self._state == State.RESPONSE:
            self._tap_timer = threading.Timer(_TAP_THRESHOLD, self._response_hold_fired)
            self._tap_timer.start()
            return

        # Stuck in LISTENING (release never fired)? Abort so next press can start fresh.
        if self._state == State.LISTENING:
            if self._on_abort_listening:
                self._on_abort_listening()
            self._state = State.IDLE
            self._update_led(State.IDLE)
            return

        # Active operation (transcribing/thinking/streaming): cancel and return to idle.
        if self._state in (State.TRANSCRIBING, State.THINKING, State.STREAMING):
            if self._cancel_allowed and not self._cancel_allowed():
                return
            self._state = State.IDLE
            self._update_led(State.IDLE)
            if self._on_cancel:
                self._on_cancel()
            return

        if self._state not in (State.IDLE, State.ERROR):
            return

        self._state = State.LISTENING
        self._update_led(State.LISTENING)
        if self._on_press:
            self._on_press()

    def _response_hold_fired(self):
        """Called 400ms after press in RESPONSE state — transition to push-to-talk."""
        if self._state == State.RESPONSE:
            self._state = State.LISTENING
            self._update_led(State.LISTENING)
            if self._on_press:
                self._on_press()

    def _handle_release(self):
        # Cancel any pending tap timer
        if self._tap_timer is not None:
            self._tap_timer.cancel()
            self._tap_timer = None

            # If still in RESPONSE state, the hold timer didn't fire — it's a tap
            if self._state == State.RESPONSE:
                if self._on_tap:
                    self._on_tap()
                return

        if self._state != State.LISTENING:
            return
        if self._on_release:
            self._on_release()
