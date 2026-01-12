# Lab 2: Designing Finite State Machines in Verilog

## Objective

Design and verify a finite state machine (FSM) controller for a vending machine.

## Specification

### Inputs
- `coin` (1 bit): Pulse when coin inserted (25 cents)
- `select` (1 bit): Pulse when item selected
- `clk`, `reset`

### Outputs
- `dispense` (1 bit): Pulse when item dispensed
- `return_change` (1 bit): Pulse when returning change
- `total` (2 bits): Current amount inserted (0, 25, 50, 75 cents)

### Behavior

Item costs 50 cents. Accept up to 75 cents, dispense item and return 25 cents change if overpaid.

## FSM State Diagram

```
States:
- IDLE (00): No money inserted
- CENTS_25 (01): 25 cents inserted
- CENTS_50 (10): 50 cents inserted
- CENTS_75 (11): 75 cents inserted
```

### State Transitions

From IDLE:
- `coin` → CENTS_25

From CENTS_25:
- `coin` → CENTS_50
- `select` → (nothing, insufficient funds)

From CENTS_50:
- `coin` → CENTS_75
- `select` → dispense, return to IDLE

From CENTS_75:
- `select` → dispense + return_change, return to IDLE

## Verilog Template

```verilog
module vending_machine(
    input clk,
    input reset,
    input coin,
    input select,
    output reg dispense,
    output reg return_change,
    output reg [1:0] total
);

    // State encoding
    localparam IDLE = 2'b00;
    localparam CENTS_25 = 2'b01;
    localparam CENTS_50 = 2'b10;
    localparam CENTS_75 = 2'b11;

    reg [1:0] state, next_state;

    // State register
    always @(posedge clk or posedge reset) begin
        if (reset)
            state <= IDLE;
        else
            state <= next_state;
    end

    // Next state logic
    always @(*) begin
        // TODO: Implement next state logic
    end

    // Output logic
    always @(*) begin
        // TODO: Implement output logic
    end

endmodule
```

## Testing

### Test Cases

1. **Normal operation**: Insert 50 cents, select, verify dispense
2. **Exact change**: Insert 25, 25, select, verify dispense
3. **Overpayment**: Insert 75 cents, select, verify dispense + change
4. **Insufficient funds**: Insert 25, select, verify no dispense
5. **Reset**: Verify system returns to IDLE

### Testbench Template

```verilog
module tb_vending_machine;
    reg clk, reset, coin, select;
    wire dispense, return_change;
    wire [1:0] total;

    vending_machine uut(
        .clk(clk),
        .reset(reset),
        .coin(coin),
        .select(select),
        .dispense(dispense),
        .return_change(return_change),
        .total(total)
    );

    // Clock generation
    always #5 clk = ~clk;

    initial begin
        // Initialize
        clk = 0; reset = 1; coin = 0; select = 0;
        #10 reset = 0;

        // Test case 1: Insert 50 cents, select
        // TODO: Implement test

        $finish;
    end
endmodule
```

## Common Errors

1. **Combinational loops**: Using blocking assignments in next-state logic
2. **Glitches**: Not registering outputs properly
3. **Race conditions**: Asynchronous inputs not synchronized to clock
4. **Incomplete case statements**: Not handling all possible states

## Timing Analysis

### Setup Time and Hold Time

**Setup time** (t_setup): Minimum time data must be stable BEFORE clock edge
**Hold time** (t_hold): Minimum time data must remain stable AFTER clock edge

Violation of either causes metastability.

### Clock-to-Q Delay

Time from clock edge to output changing: t_cq

**Maximum clock frequency**:
```
f_max = 1 / (t_cq + t_logic + t_setup)
```

Where t_logic is the longest combinational path delay.

## Submission Requirements

- Completed Verilog module
- Testbench with all 5 test cases
- Simulation waveforms
- Brief report explaining state transitions
