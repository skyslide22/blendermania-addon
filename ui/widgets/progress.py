"""
progress_task.py - generic "run this in small steps with feedback" helper for Blender.

WHAT YOU GET (for any operator that uses the mixin)
  * modal execution driven by a timer, so the UI stays responsive between steps
  * progress indicator, status bar text, wait cursor
  * ESC to cancel, with safe cleanup (also on errors and when Blender cancels it)
  * the button is greyed out while the task runs (no double clicks)
  * a result message that stays visible in your panel until cleared / next run
  * execute() fallback, so bpy.ops.your.op() from scripts still works (synchronous)

HOW TO USE
  1. Make your operator inherit ProgressTaskMixin BEFORE bpy.types.Operator.
  2. Implement task_prepare() (optional) and task_steps() (a generator).
  3. In your panel call draw_task_status(layout, <key>) where you want feedback.
  4. Call progress_task.register() / unregister() from your add-on's register().

Minimal example:

    class MYADDON_OT_do_thing(ProgressTaskMixin, bpy.types.Operator):
        bl_idname = "myaddon.do_thing"
        bl_label = "Do Thing"
        task_title = "Doing thing"

        def task_prepare(self, context):
            if not context.selected_objects:
                self.report({'ERROR'}, "Select something")
                return False            # abort, nothing starts
            return True

        def task_steps(self, context):
            objs = list(context.selected_objects)
            for i, obj in enumerate(objs):
                yield i / len(objs), f"Processing {obj.name}"   # shown BEFORE the work
                heavy_work(obj)
            self.set_result('INFO', f"Processed {len(objs)} objects")

        def task_finished(self, context):
            pass  # runs after cleanup; safe place for bpy.ops / mode switches

    # in the panel
    layout.operator("myaddon.do_thing")
    draw_task_status(layout, "myaddon.do_thing")

STEP FORMATS a generator may yield
    (fraction, "text")   fraction in 0..1
    fraction             keeps the previous text
    "text"               keeps the previous fraction

IMPORTANT
  * Everything still runs on Blender's main thread. If ONE step takes 3 seconds the UI
    freezes for 3 seconds. Make steps small, or yield more often inside long loops.
  * Don't keep references to bpy data (collections, objects, RNA structs) across yields;
    re-fetch them by name each step, as they may be invalid after UI/undo changes.
  * If your operator defines its own poll(), call super().poll(context) inside it,
    otherwise the "disable while running" behaviour is lost.
"""

from __future__ import annotations

import time  # noqa: F401  (handy for subclasses that want timing in task_steps)
import traceback
from dataclasses import dataclass
from typing import Optional

import bpy

# --------------------------------------------------------------------------------------
# Shared state (per task key). Module-level on purpose: not saved into the .blend, so a
# stale result from a previous session never shows up as if it were fresh.
# --------------------------------------------------------------------------------------

_RESULT_ICONS = {"INFO": "CHECKMARK", "WARNING": "ERROR", "ERROR": "CANCEL"}


@dataclass
class TaskState:
    running: bool = False
    fraction: float = 0.0
    text: str = ""
    level: str = "INFO"      # INFO | WARNING | ERROR  (of the last finished run)
    message: str = ""        # last result message, "" = nothing to show


_states: dict[str, TaskState] = {}
_status_token = 0            # invalidates pending "clear status bar" timers


def get_state(key: str) -> TaskState:
    return _states.setdefault(key, TaskState())


def is_running(key: str) -> bool:
    state = _states.get(key)
    return bool(state and state.running)


def clear_result(key: str) -> None:
    state = _states.get(key)
    if state and not state.running:
        state.message = ""
        state.level = "INFO"
    _tag_redraw_all()


def _tag_redraw_all() -> None:
    try:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()
    except Exception:
        pass


def _invalidate_status_timers() -> None:
    global _status_token
    _status_token += 1


def _hold_status_text(context, text: str, seconds: float) -> None:
    """Show `text` in the status bar and clear it after `seconds` (unless replaced)."""
    global _status_token
    _status_token += 1
    token = _status_token
    try:
        context.workspace.status_text_set(text)
    except Exception:
        return

    def _clear():
        if token == _status_token:
            for workspace in bpy.data.workspaces:
                workspace.status_text_set(None)
        return None  # returning None unregisters the timer

    bpy.app.timers.register(_clear, first_interval=max(seconds, 0.1))


def _normalize_step(step, last_fraction: float, last_text: str):
    """Turn whatever the generator yielded into (fraction, text)."""
    fraction, text = last_fraction, last_text
    if isinstance(step, tuple):
        if len(step) >= 1 and isinstance(step[0], (int, float)):
            fraction = float(step[0])
        if len(step) >= 2 and step[1] is not None:
            text = str(step[1])
    elif isinstance(step, (int, float)):
        fraction = float(step)
    elif isinstance(step, str):
        text = step
    return min(max(fraction, 0.0), 1.0), text


def sub_progress(gen, base: float, span: float, prefix: str = ""):
    """Run a child generator inside task_steps() with `yield from`.

    Maps the child's progress (0..1) into [base, base + span] of the parent bar,
    prepends `prefix` to its text, and returns the child's return value:

        result = yield from sub_progress(child_gen(), base=n / total, span=1 / total,
                                         prefix=f"Group {n + 1}/{total}: ")
    """
    while True:
        try:
            step = next(gen)
        except StopIteration as stop:
            return stop.value
        fraction, text = _normalize_step(step, 0.0, "")
        yield base + span * fraction, f"{prefix}{text}"


# --------------------------------------------------------------------------------------
# The mixin
# --------------------------------------------------------------------------------------

class ProgressTaskMixin:
    """Put before bpy.types.Operator in the base class list."""

    # ---- configuration (override in your subclass) ----
    task_title: str = "Working"
    task_key: str = ""                  # defaults to bl_idname; share a key to share status
    task_cancellable: bool = True       # ESC cancels
    task_wait_cursor: bool = True
    task_block_input: bool = True       # swallow other events while running
    task_timer_interval: float = 0.05   # seconds between ticks
    task_steps_per_tick: int = 1        # 1 = status text is visible while each step runs
    task_time_budget: float = 0.0       # >0: seconds of work per tick (overrides steps_per_tick);
                                        # use this with generators that yield very often
    task_status_hold: float = 6.0       # seconds the final message stays in the status bar

    # ---- hooks (override these) ----
    def task_prepare(self, context) -> Optional[bool]:
        """Validate / gather inputs. Return False to abort (report your own error)."""
        return True

    def task_steps(self, context):
        """Generator. Yield (fraction, text) between chunks of work."""
        raise NotImplementedError("task_steps() must be implemented")
        yield  # pragma: no cover  (makes this a generator for type checkers)

    def task_finished(self, context) -> None:
        """Called once after a successful run, AFTER cleanup. bpy.ops is fine here."""

    def task_cancelled(self, context) -> None:
        """Called when the user cancels with ESC."""

    # ---- helper for subclasses ----
    def set_result(self, level: str, message: str) -> None:
        """level: 'INFO' (all good), 'WARNING' (found problems) or 'ERROR'."""
        self._result = (level, message)

    # ---- internals ----
    _timer = None
    _steps = None
    _result = None
    _ui_active = False

    @classmethod
    def _task_key(cls) -> str:
        return cls.task_key or cls.bl_idname

    @classmethod
    def poll(cls, context):
        return not is_running(cls._task_key())

    def _begin(self, context) -> bool:
        self._result = None
        try:
            if self.task_prepare(context) is False:
                return False
            self._steps = iter(self.task_steps(context))
        except Exception as exc:
            traceback.print_exc()
            self.report({"ERROR"}, f"{self.task_title} failed to start: {exc}")
            return False

        state = get_state(self._task_key())
        state.running = True
        state.fraction = 0.0
        state.text = self.task_title
        state.message = ""
        _invalidate_status_timers()
        _tag_redraw_all()
        return True

    def invoke(self, context, event):
        if not self._begin(context):
            return {"CANCELLED"}

        wm = context.window_manager
        self._timer = wm.event_timer_add(self.task_timer_interval, window=context.window)
        wm.progress_begin(0, 100)
        if self.task_wait_cursor and context.window:
            context.window.cursor_modal_set("WAIT")
        self._ui_active = True
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        """Synchronous fallback (scripts, EXEC_DEFAULT). No UI feedback while running."""
        if not self._begin(context):
            return {"CANCELLED"}
        try:
            for _ in self._steps:
                pass
        except Exception as exc:
            return self._fail(context, exc)
        return self._complete(context)

    def modal(self, context, event):
        if event.type == "ESC" and self.task_cancellable:
            self._teardown(context)
            try:
                self.task_cancelled(context)
            except Exception:
                traceback.print_exc()
            self._finalize(context, "WARNING", f"{self.task_title} cancelled")
            return {"CANCELLED"}

        if event.type != "TIMER":
            return {"RUNNING_MODAL"} if self.task_block_input else {"PASS_THROUGH"}

        try:
            start = time.perf_counter()
            steps = 0
            while True:
                step = next(self._steps)
                steps += 1
                if self.task_time_budget > 0:
                    if time.perf_counter() - start >= self.task_time_budget:
                        break
                elif steps >= max(1, self.task_steps_per_tick):
                    break
            self._publish(context, step)   # once per tick, not once per step
        except StopIteration:
            return self._complete(context)
        except Exception as exc:
            return self._fail(context, exc)

        return {"RUNNING_MODAL"}

    def cancel(self, context):
        """Blender calls this when it terminates the modal itself (file load, quit...)."""
        self._teardown(context)
        self._finalize(context, "WARNING", f"{self.task_title} cancelled")

    def _publish(self, context, step) -> None:
        state = get_state(self._task_key())
        state.fraction, state.text = _normalize_step(step, state.fraction, state.text)
        percent = int(state.fraction * 100)

        context.window_manager.progress_update(percent)
        hint = "  |  ESC to cancel" if self.task_cancellable else ""
        try:
            context.workspace.status_text_set(
                f"{self.task_title}: {state.text}  |  {percent}%{hint}"
            )
        except Exception:
            pass
        _tag_redraw_all()

    def _teardown(self, context) -> None:
        """Idempotent: safe to call from modal, cancel, error paths and execute."""
        wm = context.window_manager
        if self._timer is not None:
            try:
                wm.event_timer_remove(self._timer)
            except Exception:
                pass
            self._timer = None

        if self._ui_active:
            try:
                wm.progress_end()
            except Exception:
                pass
            try:
                context.workspace.status_text_set(None)
            except Exception:
                pass
            if self.task_wait_cursor and context.window:
                try:
                    context.window.cursor_modal_restore()
                except Exception:
                    pass
            self._ui_active = False

        get_state(self._task_key()).running = False
        self._steps = None

    def _complete(self, context):
        self._teardown(context)
        try:
            self.task_finished(context)
        except Exception as exc:
            return self._fail(context, exc)
        level, message = self._result or ("INFO", f"{self.task_title} finished")
        self._finalize(context, level, message)
        return {"FINISHED"}

    def _fail(self, context, exc: Exception):
        traceback.print_exc()
        self._teardown(context)
        self._finalize(context, "ERROR", f"{self.task_title} failed: {exc}")
        return {"CANCELLED"}

    def _finalize(self, context, level: str, message: str) -> None:
        state = get_state(self._task_key())
        state.running = False
        state.level = level
        state.message = message
        state.fraction = 1.0 if level != "ERROR" else state.fraction

        try:
            self.report({level}, message)
        except Exception:
            pass
        _hold_status_text(context, message, self.task_status_hold)
        _tag_redraw_all()


# --------------------------------------------------------------------------------------
# Panel helper
# --------------------------------------------------------------------------------------

def draw_task_status(layout, key: str, *, show_bar: bool = True, clearable: bool = True) -> None:
    """Draw a progress bar while running, otherwise the last result (until cleared).

    `key` is the task key: the operator's bl_idname unless you set task_key.
    """
    state = _states.get(key)
    if state is None:
        return

    if state.running:
        percent = int(state.fraction * 100)
        if show_bar and hasattr(layout, "progress"):  # UILayout.progress: newer Blender
            layout.progress(factor=state.fraction, type="BAR", text=state.text or "Working...")
        else:
            layout.label(text=f"{state.text} ({percent}%)", icon="TIME")
        return

    if state.message:
        row = layout.row(align=True)
        row.label(text=state.message, icon=_RESULT_ICONS.get(state.level, "INFO"))
        if clearable:
            op = row.operator("wm.progress_task_clear", text="", icon="X", emboss=False)
            op.key = key


# --------------------------------------------------------------------------------------
# Small operator used by the "X" button in draw_task_status
# --------------------------------------------------------------------------------------

class PROGRESSTASK_OT_clear(bpy.types.Operator):
    bl_idname = "wm.progress_task_clear"
    bl_label = "Clear Result"
    bl_options = {"INTERNAL"}

    key: bpy.props.StringProperty()

    def execute(self, context):
        clear_result(self.key)
        return {"FINISHED"}


_classes = (PROGRESSTASK_OT_clear,)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
    _states.clear()
