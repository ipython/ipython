"""End-to-end checks for the %promote proof of concept.

Drives a real `ipython` terminal session under pexpect, promotes it to a
kernel, attaches a jupyter_client (standing in for a notebook), and verifies
both modes:

Hand-off mode (default %promote):
- the terminal REPL ends; the process becomes a kernel;
- client executions run on the MAIN thread (the point of hand-off);
- signal handlers are installable from client code (main-thread-only API);
- execute_result / stream / display_data all arrive on iopub;
- interrupt_request over the control channel interrupts a busy execution
  (SIGINT -> KeyboardInterrupt, only possible with main-thread execution);
- shutdown_request terminates the process cleanly.

Share mode (%promote --share):
- the terminal REPL stays interactive after promotion;
- the client executes against the terminal's namespace (execute_result on iopub);
- print() from client executions arrives as a stream message on iopub;
- state assigned by the client is visible back at the terminal;
- with the traitlets SingletonScope extension installed
  (https://github.com/Carreau/traitlets/tree/multiton), display() publishes
  display_data on iopub (on stock traitlets the PoC's singleton swap routes
  display() to the terminal instead, and this check is skipped).

Run directly: python test_promote_e2e.py   (requires pexpect, ipykernel)
"""
import os
import sys
import tempfile
import time

import pexpect

POC_DIR = os.path.dirname(os.path.abspath(__file__))


def spawn_promoted(promote_args):
    workdir = tempfile.mkdtemp(prefix="promote-e2e-")
    ext_dir = os.path.join(workdir, "external")

    env = dict(os.environ)
    env["PYTHONPATH"] = POC_DIR + os.pathsep + env.get("PYTHONPATH", "")
    env["JUPYTER_RUNTIME_DIR"] = os.path.join(workdir, "runtime")

    child = pexpect.spawn(
        sys.executable,
        ["-m", "IPython", "--no-banner", "--colors=nocolor"],
        env=env,
        encoding="utf-8",
        timeout=60,
        dimensions=(40, 120),
    )
    child.expect(r"In \[1\]:")
    child.sendline("x = 10")
    child.expect(r"In \[2\]:")
    child.sendline("%load_ext promote_kernel")
    child.expect(r"In \[3\]:")
    child.sendline("%promote --external-dir " + ext_dir + " " + promote_args)
    child.expect("Connection file: (\\S+kernel-\\d+\\.json)")
    cf = child.match.group(1).splitlines()[0].strip()
    deadline = time.time() + 30
    while not os.path.exists(cf):
        assert time.time() < deadline, "connection file never appeared"
        time.sleep(0.2)
    return child, cf


def attach(cf):
    from jupyter_client import BlockingKernelClient

    kc = BlockingKernelClient(connection_file=cf)
    kc.load_connection_file()
    kc.start_channels()
    kc.wait_for_ready(timeout=20)
    return kc


def run(kc, code, reply_timeout=20):
    kc.execute(code)
    reply = kc.get_shell_msg(timeout=reply_timeout)
    streams, results, display_data = [], [], []
    deadline = time.time() + 8
    while time.time() < deadline:
        try:
            m = kc.get_iopub_msg(timeout=1)
        except Exception:
            continue
        if m["msg_type"] == "stream":
            streams.append(m["content"]["text"])
        elif m["msg_type"] == "execute_result":
            results.append(m["content"]["data"].get("text/plain"))
        elif m["msg_type"] == "display_data":
            display_data.append(m["content"]["data"])
        elif m["msg_type"] == "status" and m["content"]["execution_state"] == "idle":
            # allow one buffered stream flush after idle, then drain
            time.sleep(0.5)
            try:
                while True:
                    m2 = kc.get_iopub_msg(timeout=0.3)
                    if m2["msg_type"] == "stream":
                        streams.append(m2["content"]["text"])
            except Exception:
                pass
            break
    return reply["content"], streams, results, display_data


def test_handoff():
    print("--- hand-off mode (default) ---")
    child, cf = spawn_promoted("")
    kc = attach(cf)
    print("client attached")

    reply, _, results, _ = run(kc, "x + 5")
    assert reply["status"] == "ok" and results == ["15"], (reply, results)
    print("client exec sees terminal namespace (x + 5 -> 15)")

    reply, _, results, _ = run(kc, "import threading; threading.current_thread().name")
    assert results == ["'MainThread'"], results
    print("client code executes on the MAIN thread")

    reply, _, results, _ = run(
        kc,
        "import signal; signal.signal(signal.SIGALRM, signal.SIG_DFL); 'signal-ok'",
    )
    assert reply["status"] == "ok" and results == ["'signal-ok'"], (reply, results)
    print("signal handlers installable from client code (main-thread-only API)")

    reply, streams, _, _ = run(kc, "print('streamed')")
    assert any("streamed" in s for s in streams), streams
    print("client print() -> stream message on iopub")

    reply, _, _, display_data = run(
        kc, "from IPython.display import display, HTML; display(HTML('<b>rich</b>'))"
    )
    assert reply["status"] == "ok" and any("text/html" in d for d in display_data), (
        reply,
        display_data,
    )
    print("client display() -> display_data on iopub")

    # interrupt a busy execution via the control channel: only works because
    # execution owns the main thread (interrupt_request -> SIGINT ->
    # default_int_handler -> KeyboardInterrupt in the user code).
    kc.execute("import time; time.sleep(120)")
    time.sleep(1)
    msg = kc.session.msg("interrupt_request", {})
    kc.control_channel.send(msg)
    reply = kc.get_shell_msg(timeout=20)
    assert reply["content"]["status"] == "error", reply["content"]
    assert reply["content"]["ename"] == "KeyboardInterrupt", reply["content"]["ename"]
    print("interrupt_request -> KeyboardInterrupt in busy execution")

    kc.shutdown()
    kc.stop_channels()
    child.expect(pexpect.EOF, timeout=30)
    print("shutdown_request -> process exited cleanly")


def test_share():
    print("--- share mode (--share) ---")
    child, cf = spawn_promoted("--share")
    child.expect(r"In \[4\]:")
    child.sendline("y = x + 5")
    child.expect(r"In \[5\]:")
    print("terminal still interactive after promote")

    kc = attach(cf)
    print("client attached")

    reply, _, results, _ = run(kc, "x + y")
    assert reply["status"] == "ok" and results == ["25"], (reply, results)
    print("client exec 'x + y' -> 25 (execute_result on iopub)")

    reply, streams, _, _ = run(kc, "print('streamed'); z = 99")
    assert reply["status"] == "ok" and any("streamed" in s for s in streams), (
        reply,
        streams,
    )
    print("client print() -> stream message on iopub")

    try:
        from traitlets.config import SingletonScope  # noqa: F401

        has_scope = True
    except ImportError:
        has_scope = False
    reply, _, _, display_data = run(
        kc, "from IPython.display import display, HTML; display(HTML('<b>rich</b>'))"
    )
    assert reply["status"] == "ok", reply
    if has_scope:
        assert any("text/html" in d for d in display_data), display_data
        print("client display() -> display_data on iopub (SingletonScope mode)")
    else:
        print(
            "display_data on iopub: %s (stock traitlets; expected to be missing)"
            % bool(display_data)
        )

    kc.stop_channels()

    child.sendline("print('z is', z)")
    child.expect("z is 99", timeout=15)
    print("terminal sees client-assigned variable")
    child.close(force=True)


if __name__ == "__main__":
    test_handoff()
    test_share()
    print("E2E OK")
