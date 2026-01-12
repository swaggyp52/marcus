# Homework 3: Timing Analysis and Sequential Circuits

Due: Next Friday, 11:59 PM

## Problem 1: Setup and Hold Time Violations

Given a flip-flop with:
- t_setup = 0.5 ns
- t_hold = 0.2 ns
- t_cq = 0.8 ns

And a combinational logic block with delay = 3.2 ns.

a) What is the minimum clock period?
b) If the clock period is 5 ns, what is the setup time margin?
c) If data arrives 0.1 ns before the clock edge, is there a hold time violation?

## Problem 2: Metastability

Explain what happens when setup or hold time requirements are violated. Why is this a problem in asynchronous designs?

Sketch the output waveform of a flip-flop experiencing metastability.

## Problem 3: FSM Design

Design an FSM that detects the sequence "1011" in a serial bit stream.

a) Draw the state diagram
b) Create the state transition table
c) Write the next-state and output logic equations
d) How many flip-flops are needed for the state register?

## Problem 4: Cache Coherence (Bonus)

In a dual-core system with MESI protocol:

Initial state: Both caches have address X in Shared (S) state.

Sequence of operations:
1. CPU 0 writes to X
2. CPU 1 reads X
3. CPU 0 writes to X again
4. CPU 1 writes to X

For each operation, show:
- State transitions in both caches
- Whether a bus transaction occurs
- Type of transaction (if any)

## Problem 5: Critical Path

Given this circuit:

```
Input → [AND gate, 2ns] → [OR gate, 1.5ns] → [XOR gate, 2.5ns] → Output
     ↘ [NOT gate, 1ns] ↗
```

a) Identify the critical path
b) What is the minimum clock period if this is the combinational logic between two registers?
c) If we need to run at 200 MHz, can this design meet timing?

## Submission Format

- PDF with all solutions
- Show all work and intermediate steps
- Include diagrams for FSM and waveforms
- Clearly label final answers
