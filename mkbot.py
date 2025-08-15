import os
import sys
import time
from dataclasses import dataclass, field

import psutil
from watchdog.observers.api import BaseObserverSubclassCallable
from watchdog.tricks import AutoRestartTrick
from watchdog.utils import WatchdogShutdown

if not sys.platform.startswith("win"):

    def kill_process(pid, stop_signal):
        os.killpg(os.getpgid(pid), stop_signal)

else:

    def kill_process(pid, stop_signal):
        try:
            parent = psutil.Process(pid)
        except psutil.NoSuchProcess:
            return

        children = parent.children(recursive=True)

        os.kill(pid, stop_signal)

        for child in children:
            os.kill(child.pid, stop_signal)


class MKBotAutoRestartTrick(AutoRestartTrick):
    def _restart_process(self):
        print("\n====== Restart MK Bot Discord Host ======\n")
        return super()._restart_process()

    def _start_process(self):
        # print("<====== Start MK Bot Discord Host ======>")
        return super()._start_process()

    def _stop_process(self):
        # Ensure the body of the function is not run in parallel in different threads.
        with self._stopping_lock:
            if self._is_process_stopping:
                return
            self._is_process_stopping = True

        try:
            if self.process_watcher is not None:
                self.process_watcher.stop()
                self.process_watcher = None

            if self.process is not None:
                try:
                    kill_process(self.process.pid, self.stop_signal)
                except OSError:
                    # Process is already gone
                    pass
                else:
                    kill_time = time.time() + self.kill_after
                    # print(">>> KILL", self.process.poll(), self.process.pid)
                    while time.time() < kill_time:
                        if self.process.poll() is not None:
                            break
                        time.sleep(0.25)
                    else:
                        try:
                            kill_process(self.process.pid, 9)
                        except OSError:
                            # Process is already gone
                            pass
                # print(">>> KILL", self.process.poll())
                self.process = None
        finally:
            self._is_process_stopping = False


def parse_patterns(patterns_spec, ignore_patterns_spec, separator=";"):
    """
    Parses pattern argument specs and returns a two-tuple of
    (patterns, ignore_patterns).
    """
    patterns = patterns_spec.split(separator)
    ignore_patterns = ignore_patterns_spec.split(separator)
    if ignore_patterns == [""]:
        ignore_patterns = []
    return (patterns, ignore_patterns)


def observe_with(observer, event_handler, pathnames, recursive):
    """
    Single observer thread with a scheduled path and event handler.

    :param observer:
        The observer thread.
    :param event_handler:
        Event handler which will be called in response to file system events.
    :param pathnames:
        A list of pathnames to monitor.
    :param recursive:
        ``True`` if recursive; ``False`` otherwise.
    """
    for pathname in set(pathnames):
        observer.schedule(event_handler, pathname, recursive)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except WatchdogShutdown:
        observer.stop()
    observer.join()


@dataclass
class AutoRestartArgs:
    command: str
    command_args: list[str]
    directories: list[str] = field(default_factory=list)
    patterns: str = "*"
    ignore_patterns: str = ""
    ignore_directories: bool = False
    recursive: bool = True
    timeout: float = 0.0
    kill_after: float = 20.0
    debounce_interval: float = 0.5
    restart_on_command_exit: bool = False
    signal: str = "SIGINT"
    debug_force_polling: bool = False


def auto_restart(args: AutoRestartArgs):
    """
    Command to start a long-running subprocess and restart it on matched events.
    """

    Observer: BaseObserverSubclassCallable
    if args.debug_force_polling:
        from watchdog.observers.polling import PollingObserver as Observer
    else:
        from watchdog.observers import Observer

    import signal

    if not args.directories:
        args.directories = ["."]

    # Allow either signal name or number.
    if isinstance(args.signal, str) and args.signal.startswith("SIG"):
        stop_signal = getattr(signal, args.signal)
    else:
        stop_signal = int(args.signal)

    # Handle termination signals by raising a semantic exception which will
    # allow us to gracefully unwind and stop the observer
    termination_signals = {signal.SIGTERM, signal.SIGINT}

    if hasattr(signal, "SIGHUP"):
        termination_signals.add(signal.SIGHUP)

    def handler_termination_signal(_signum, _frame):
        # Neuter all signals so that we don't attempt a double shutdown
        for signum in termination_signals:
            signal.signal(signum, signal.SIG_IGN)
        raise WatchdogShutdown

    for signum in termination_signals:
        signal.signal(signum, handler_termination_signal)

    patterns, ignore_patterns = parse_patterns(args.patterns, args.ignore_patterns)
    command = [args.command]
    command.extend(args.command_args)
    handler = MKBotAutoRestartTrick(
        command=command,
        patterns=patterns,
        ignore_patterns=ignore_patterns,
        ignore_directories=args.ignore_directories,
        stop_signal=stop_signal,
        kill_after=args.kill_after,
        debounce_interval_seconds=args.debounce_interval,
        restart_on_command_exit=args.restart_on_command_exit,
    )
    handler.start()
    observer = Observer(timeout=args.timeout)
    try:
        observe_with(observer, handler, args.directories, args.recursive)
    except WatchdogShutdown:
        pass
    finally:
        handler.stop()


def running_in_vscode():
    if "TERM_PROGRAM" in os.environ.keys() and os.environ["TERM_PROGRAM"] == "vscode":
        return True

    return False


if __name__ == "__main__":
    if os.path.isfile(".venv/Scripts/python.exe"):
        cmd = "poetry"
        if running_in_vscode() and "--debug" in sys.argv:
            cmd_args = [
                "run",
                "python",
                "src/bot/discord_host.py",
                "--debugpy",
            ]
        else:
            cmd_args = ["run", "python", "src/bot/discord_host.py"]

    else:
        cmd = "python"
        if running_in_vscode() and "--debug" in sys.argv:
            cmd_args = [
                "src/bot/discord_host.py",
                "--debugpy",
            ]
        else:
            cmd_args = ["src/bot/discord_host.py"]

    auto_restart(
        AutoRestartArgs(
            cmd,
            cmd_args,
            ["src/bot", "src/lib"],
            "*.py",
        )
    )
else:
    os.chdir("src/bot")
    sys.path.append("../lib")

    from mgylabs.db.database import run_migrations, scope_manager
    from mgylabs.db.paths import DB_URL, SCRIPT_DIR

    run_migrations(SCRIPT_DIR, DB_URL, echo=True)

    scope_manager.set_session_id()
