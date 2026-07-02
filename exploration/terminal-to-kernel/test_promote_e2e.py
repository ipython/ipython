"""End-to-end check for the %promote proof of concept.

Drives a real `ipython` terminal session under pexpect, promotes it to a
kernel, attaches a jupyter_client (standing in for a notebook), and verifies:

- the connection file is written and loadable;
- the terminal REPL stays interactive after promotion;
- the client executes against the terminal's namespace (execute_result on iopub);
- print() from client executions arrives as a stream message on iopub;
- state assigned by the client is visible back at the terminal.

Run directly: python test_promote_e2e.py   (requires pexpect, ipykernel)
"""
import os
import sys
import tempfile
import time

import pexpect

POC_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
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
    child.sendline("%promote --external-dir " + ext_dir)
    child.expect("Connection file: (\\S+kernel-\\d+\\.json)")
    cf = child.match.group(1).splitlines()[0].strip()
    print("promoted; connection file:", cf)
    child.expect(r"In \[4\]:")

    child.sendline("y = x + 5")
    child.expect(r"In \[5\]:")
    print("terminal still interactive after promote")

    from jupyter_client import BlockingKernelClient

    kc = BlockingKernelClient(connection_file=cf)
    kc.load_connection_file()
    kc.start_channels()
    kc.wait_for_ready(timeout=20)
    print("client attached")

    def run(code):
        kc.execute(code)
        reply = kc.get_shell_msg(timeout=20)
        streams, results = [], []
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
            elif (
                m["msg_type"] == "status"
                and m["content"]["execution_state"] == "idle"
            ):
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
        return reply["content"]["status"], streams, results

    status, _, results = run("x + y")
    assert status == "ok" and results == ["25"], (status, results)
    print("client exec 'x + y' -> 25 (execute_result on iopub)")

    status, streams, _ = run("print('streamed'); z = 99")
    assert status == "ok" and any("streamed" in s for s in streams), (status, streams)
    print("client print() -> stream message on iopub")

    kc.stop_channels()

    child.sendline("print('z is', z)")
    child.expect("z is 99", timeout=15)
    print("terminal sees client-assigned variable")

    child.close(force=True)
    print("E2E OK")


if __name__ == "__main__":
    main()
