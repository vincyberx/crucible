"""Exact solver for reason-08: round-robin CPU scheduling with I/O and context switches.

Unit-step simulation. At every integer instant t the events are handled in the order fixed
by rule 7 of task.md: (i) I/O completion, (ii) arrivals, (iii) the process leaving the CPU,
(iv) dispatch. Then one time unit elapses for the CPU (switch or run) and the I/O device.
"""

QUANTUM = 3
SWITCH = 1

PROCESSES = {
    # name: (arrival, [CPU, I/O, CPU, ...])
    "A": (0, [3, 2, 6]),
    "B": (6, [7]),
    "C": (11, [5, 3, 2]),
    "D": (13, [8, 7, 2]),
    "E": (14, [3, 7, 7]),
}


def simulate():
    names = sorted(PROCESSES)
    phase = {p: 0 for p in names}                  # index of the current burst
    left = {p: PROCESSES[p][1][0] for p in names}  # units left in the current burst
    ready = []
    io_wait = []
    io_cur = None          # process on the I/O device
    cpu = None             # process owning the CPU (switching or running)
    switch_left = 0        # > 0 while a context switch is in progress
    used = 0               # running units used in the current dispatch
    last_ran = None        # process that most recently ran on the CPU
    finished = {}
    t = 0
    while len(finished) < len(names):
        assert t < 1000
        # (i) I/O completion
        if io_cur is not None and left[io_cur] == 0:
            p = io_cur
            phase[p] += 1
            left[p] = PROCESSES[p][1][phase[p]]
            ready.append(p)
            io_cur = io_wait.pop(0) if io_wait else None
        # (ii) arrivals
        for p in names:
            if PROCESSES[p][0] == t:
                ready.append(p)
        # (iii) the process leaving the CPU at t
        if cpu is not None and switch_left == 0:
            p = cpu
            if left[p] == 0:  # burst finished (takes precedence over quantum expiry)
                cpu = None
                if phase[p] == len(PROCESSES[p][1]) - 1:
                    finished[p] = t
                else:
                    phase[p] += 1
                    left[p] = PROCESSES[p][1][phase[p]]
                    if io_cur is None:
                        io_cur = p
                    else:
                        io_wait.append(p)
            elif used == QUANTUM:
                cpu = None
                ready.append(p)
        # (iv) dispatch
        if cpu is None and ready:
            cpu = ready.pop(0)
            used = 0
            switch_left = 0 if cpu == last_ran else SWITCH
            if switch_left == 0:
                last_ran = cpu
        # one time unit elapses
        if cpu is not None:
            if switch_left > 0:
                switch_left -= 1
            else:
                left[cpu] -= 1
                used += 1
                last_ran = cpu
        if io_cur is not None:
            left[io_cur] -= 1
        t += 1
    return finished


def main():
    done = simulate()
    print(",".join("%s=%d" % (p, done[p]) for p in sorted(done)))


if __name__ == "__main__":
    main()
