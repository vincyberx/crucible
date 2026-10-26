# Task: round-robin scheduler with I/O and context switches

A computer has **one CPU** and **one I/O device**. Time is counted in whole units starting
at t = 0. Five processes alternate CPU bursts and I/O bursts, always starting and ending
with a CPU burst:

| Process | Arrival time | Bursts, in order |
|---------|--------------|------------------|
| A | 0 | CPU 3, I/O 2, CPU 6 |
| B | 6 | CPU 7 |
| C | 11 | CPU 5, I/O 3, CPU 2 |
| D | 13 | CPU 8, I/O 7, CPU 2 |
| E | 14 | CPU 3, I/O 7, CPU 7 |

## Scheduling rules

1. **Ready queue.** There is a single first-in-first-out ready queue. A process joins it
   at the tail when it arrives, when its I/O burst ends, and when it is preempted.
2. **Dispatch.** Whenever the CPU is free and the ready queue is not empty, the
   dispatcher removes the process at the head of the queue and gives it the CPU.
3. **Context switch.** Giving the CPU to a process costs a context switch of **1 time
   unit**, during which the CPU is busy and no process runs; the process starts running
   when the switch ends. There is **no** context switch when the process being dispatched
   is the same process that most recently ran on the CPU, even if the CPU was idle in
   between. The very first dispatch of the simulation does cost a switch. The process is
   chosen when the switch begins, and nothing that happens during the switch changes it.
4. **Quantum.** Each dispatch gives a process a quantum of **3 units of running time**
   (switch time does not count). A process that has run for 3 units in the current
   dispatch and still has work left in its current CPU burst is preempted and joins the
   tail of the ready queue. If a CPU burst ends at exactly the moment the quantum runs
   out, the process is not preempted: its burst is simply over. Every dispatch starts a
   fresh quantum.
5. **I/O.** When a CPU burst ends and the process has an I/O burst next, the process
   requests the I/O device. If the device is free, the I/O burst starts immediately;
   otherwise the process waits in a first-in-first-out I/O queue. The device serves one
   process at a time and never preempts; when it finishes a burst, the next waiting
   process starts on it at that same instant. When a process's I/O burst ends, the process
   joins the tail of the ready queue.
6. **Termination.** A process terminates at the instant its last CPU burst ends.
7. **Simultaneous events.** When several things happen at the same instant, they are
   handled in this order:
   1. I/O completions: the process whose I/O burst ended joins the ready queue, and the
      next process waiting for the device (if any) starts its I/O burst;
   2. arrivals: newly arriving processes join the ready queue, in alphabetical order if
      there are several;
   3. the process leaving the CPU at that instant: a preempted process joins the ready
      queue; a process whose CPU burst ended requests the I/O device (rule 5) or terminates;
   4. finally, if the CPU is free, the dispatcher acts (rule 2).

**Question:** at what time does each process terminate?

## Deliverable

Write your reasoning to `ANSWER.md` in the current directory. The file must end with a
final line of exactly this form, giving the five termination times in alphabetical order
of process name, separated by commas with no spaces, e.g. `ANSWER: A=10,B=20,C=30,D=40,E=50`:

```
ANSWER: <value>
```
