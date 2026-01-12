"""
Marcus v0.3 - Test Data Loader
Generates realistic synthetic academic content for testing search functionality.

Usage:
    python scripts/load_test_data.py
    python scripts/load_test_data.py --download-public  (requires Online Mode)
"""

import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from marcus_app.core.database import SessionLocal, init_db
from marcus_app.core.models import Class, Assignment, Artifact, ExtractedText, SystemConfig, TextChunk
from marcus_app.services.chunking_service import ChunkingService

# Paths
BASE_PATH = Path(__file__).parent.parent
VAULT_PATH = BASE_PATH / "vault"
VAULT_PATH.mkdir(exist_ok=True)


# ============================================================================
# SYNTHETIC COURSE CONTENT
# ============================================================================

PHYS214_CONTENT = {
    "Textbook_Chapter3_Rotational_Motion.md": """# Chapter 3: Rotational Motion and Dynamics

## 3.1 Introduction to Rotational Motion

Rotational motion describes the movement of objects around an axis. Unlike linear motion, where we use position, velocity, and acceleration, rotational motion uses angular position (θ), angular velocity (ω), and angular acceleration (α).

### Key Concepts

**Angular Displacement**: The change in angular position, measured in radians.

**Angular Velocity**: The rate of change of angular position. For a point on a rotating object, ω = Δθ/Δt.

**Angular Acceleration**: The rate of change of angular velocity, α = Δω/Δt.

## 3.2 Torque and Moment of Inertia

**Torque** (τ) is the rotational equivalent of force. It causes angular acceleration and is calculated as:

τ = r × F = rF sin(θ)

where r is the distance from the axis of rotation, F is the applied force, and θ is the angle between r and F.

**Moment of Inertia** (I) is the rotational equivalent of mass. It depends on both the mass distribution and the axis of rotation.

For a point mass: I = mr²
For a solid cylinder: I = (1/2)MR²
For a solid sphere: I = (2/5)MR²

### Common Mistake Alert

Students often confuse torque and moment. Torque is a force that causes rotation. Moment of inertia is a property of the object's mass distribution. They are related through Newton's second law for rotation:

τ = Iα

## 3.3 Rotational Kinetic Energy

An object rotating about an axis has rotational kinetic energy:

KE_rot = (1/2)Iω²

This is analogous to linear kinetic energy KE = (1/2)mv².

### Energy Conservation in Rotation

Total mechanical energy includes both translational and rotational components:

E_total = (1/2)mv² + (1/2)Iω² + mgh

## 3.4 Angular Momentum

Angular momentum (L) is the rotational analog of linear momentum:

L = Iω

**Conservation of Angular Momentum**: In the absence of external torques, angular momentum is conserved. This explains why ice skaters spin faster when they pull their arms in (reducing I, increasing ω).

## 3.5 Problem-Solving Strategy

1. Identify the axis of rotation
2. Calculate moment of inertia for the object
3. Determine all torques acting on the system
4. Apply τ_net = Iα
5. Use kinematics to solve for unknowns
6. Check units and reasonableness

### Common Errors to Avoid

- Forgetting to use radians (not degrees) for angular measurements
- Using the wrong moment of inertia formula for the object shape
- Not accounting for the perpendicular component of force when calculating torque
- Mixing up linear and angular quantities (v vs ω, a vs α)
""",

    "Lab1_Rotational_Inertia.md": """# Lab 1: Measuring Rotational Inertia

## Objective

Determine the moment of inertia of various objects experimentally and compare with theoretical predictions.

## Equipment

- Rotational apparatus with photogate
- Set of cylindrical masses
- Solid disk
- Hollow cylinder
- Stopwatch
- Calipers

## Procedure

### Part A: Solid Disk

1. Measure the mass (M) and radius (R) of the solid disk using the balance and calipers
2. Mount the disk on the rotational apparatus
3. Apply a known torque by hanging a mass from a string wound around the disk
4. Measure the angular acceleration using the photogate
5. Calculate experimental moment of inertia: I_exp = τ/α
6. Compare with theoretical: I_theory = (1/2)MR²

### Part B: Hollow Cylinder

Repeat procedure for the hollow cylinder.
Theoretical formula: I = (1/2)M(R₁² + R₂²) where R₁ is inner radius, R₂ is outer radius.

## Safety Notes

- Ensure the apparatus is securely mounted before applying torque
- Keep fingers clear of rotating parts
- Use caution when handling masses

## Data Analysis

Calculate percent error between experimental and theoretical values:

% Error = |I_exp - I_theory| / I_theory × 100%

Typical sources of error:
- Friction in bearings
- Air resistance
- Mass of string not accounted for
- Measurement uncertainty in radius

## Questions

1. Why do we use angular acceleration instead of angular velocity to determine I?
2. How would friction affect your calculated value of I?
3. Which object should have the larger moment of inertia: a solid disk or a hollow cylinder of the same mass and outer radius? Why?
""",

    "Homework1_Rotational_Dynamics.md": """# Homework 1: Rotational Dynamics Problems

Due: Friday, 11:59 PM

## Problem 1: Torque Calculation

A wrench 0.30 m long is used to tighten a bolt. The force is applied at an angle of 60° to the wrench handle with a magnitude of 200 N.

a) Calculate the torque applied to the bolt.
b) What force would be required if applied perpendicular to the wrench?

## Problem 2: Moment of Inertia

A solid sphere of radius 0.15 m and mass 2.0 kg rotates about an axis through its center.

a) Calculate the moment of inertia.
b) If the sphere is rotating at 5.0 rad/s, what is its rotational kinetic energy?
c) How much work was required to bring it up to this angular velocity from rest?

## Problem 3: Angular Momentum Conservation

A figure skater spinning at 2.0 rev/s has a moment of inertia of 4.0 kg·m². She pulls her arms in, reducing her moment of inertia to 2.5 kg·m².

a) What is her new angular velocity?
b) How does her rotational kinetic energy change?
c) Where does this energy come from?

## Problem 4: Compound Motion

A solid cylinder of mass 5.0 kg and radius 0.10 m rolls without slipping down an incline of height 2.0 m.

a) Find the cylinder's velocity at the bottom.
b) What fraction of its kinetic energy is rotational?
c) Compare this to a solid sphere of the same mass and radius. Which reaches the bottom faster?

## Submission Guidelines

- Show all work
- Include units in every step
- Box final answers
- Check reasonableness of results
"""
}

CYENG350_CONTENT = {
    "Lecture_Threat_Modeling.md": """# Lecture 7: Threat Modeling and Security Analysis

## What is Threat Modeling?

Threat modeling is a structured approach to identifying, quantifying, and addressing security risks in a system. It answers four key questions:

1. What are we building?
2. What can go wrong?
3. What should we do about it?
4. Did we do a good job?

## Common Threat Modeling Frameworks

### STRIDE

STRIDE is a mnemonic for six threat categories:

- **Spoofing**: Impersonating someone or something else
- **Tampering**: Modifying data or code
- **Repudiation**: Claiming you didn't do something you actually did
- **Information Disclosure**: Exposing information to unauthorized parties
- **Denial of Service**: Degrading or denying service to users
- **Elevation of Privilege**: Gaining capabilities without authorization

### DREAD (Deprecated but worth knowing)

Used for risk rating:
- Damage potential
- Reproducibility
- Exploitability
- Affected users
- Discoverability

## Secure Boot Process

Secure boot ensures that a system boots only trusted software.

### Chain of Trust

1. **Boot ROM** (immutable, burned into chip)
   - Contains manufacturer's public key
   - Verifies bootloader signature

2. **Bootloader**
   - Signed by manufacturer
   - Verifies operating system kernel signature

3. **OS Kernel**
   - Signed and trusted
   - Loads only signed drivers and services

### Common Attacks on Boot Process

**Evil Maid Attack**: Physical access attack where attacker modifies bootloader
**Mitigation**: Secure boot with TPM-based attestation

**Rollback Attack**: Replacing newer signed software with older vulnerable version
**Mitigation**: Version checking and anti-rollback counters

## Side-Channel Attacks

Side-channel attacks exploit information leaked through physical implementation rather than algorithmic weaknesses.

### Types of Side-Channels

**Timing Side-Channels**
- Measuring execution time reveals secret information
- Example: AES cache-timing attacks reveal encryption keys

**Power Analysis**
- Simple Power Analysis (SPA): Direct observation of power consumption
- Differential Power Analysis (DPA): Statistical analysis of power traces

**Electromagnetic (EM) Side-Channels**
- Measuring EM radiation during crypto operations
- Can recover keys from several meters away

### Countermeasures

1. **Constant-time implementations**: Ensure operations take same time regardless of data
2. **Masking**: Randomize intermediate values
3. **Noise injection**: Add random operations to obscure signal
4. **Hardware countermeasures**: Shielding, power filtering

## Trusted Execution Environments (TEE)

A TEE is an isolated execution environment that provides security features:

- **ARM TrustZone**: Separates "secure world" from "normal world"
- **Intel SGX**: Isolated memory enclaves
- **AMD SEV**: Encrypted virtual machines

### Use Cases

- DRM and content protection
- Mobile payment systems
- Biometric authentication
- Secure key storage

## Common Mistake: Security Through Obscurity

Relying on secrecy of design rather than strength of cryptography is a critical error.

**Kerckhoffs's Principle**: A cryptosystem should be secure even if everything about the system, except the key, is public knowledge.

## Practical Threat Modeling Exercise

For a simple IoT device (smart lock):

1. **Asset identification**: User credentials, access logs, encryption keys
2. **Attack surface**: Bluetooth interface, firmware update mechanism, physical access
3. **Threats**:
   - Spoofing: Replay attack on unlock command
   - Tampering: Firmware modification
   - Information Disclosure: Sniffing Bluetooth traffic
4. **Mitigations**:
   - Use challenge-response authentication
   - Implement secure boot
   - Encrypt all wireless communications
"""
,

    "Lab_Side_Channel_Analysis.md": """# Lab 3: Side-Channel Analysis

## Objective

Demonstrate timing side-channel vulnerability in a naive password comparison function and implement a secure alternative.

## Background

Many authentication systems check passwords character-by-character and return immediately when a mismatch is found. This creates a timing side-channel: the time taken reveals how many characters matched.

## Part 1: Vulnerable Implementation

```python
def insecure_compare(password, user_input):
    if len(password) != len(user_input):
        return False
    for i in range(len(password)):
        if password[i] != user_input[i]:
            return False  # Early return leaks information!
    return True
```

### Attack Strategy

1. Measure time for each possible first character
2. Character that takes longest is likely correct
3. Repeat for second character, then third, etc.

## Part 2: Timing Measurements

Use high-resolution timer to measure comparison time:

```python
import time

def measure_timing(password, guess, iterations=1000):
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        insecure_compare(password, guess)
        end = time.perf_counter()
        times.append(end - start)
    return sum(times) / len(times)
```

## Part 3: Secure Implementation

```python
def secure_compare(password, user_input):
    if len(password) != len(user_input):
        # Still check length, but pad to constant time
        user_input += 'x' * (len(password) - len(user_input))

    result = 0
    for i in range(len(password)):
        # Always compare all characters
        result |= ord(password[i]) ^ ord(user_input[i])

    return result == 0
```

### Why This Works

- Always iterates through entire password
- Uses bitwise OR to accumulate differences
- No early returns
- Constant-time execution

## Expected Results

### Vulnerable Version
- Timing increases as more characters match
- Clear correlation between correct prefix length and execution time

### Secure Version
- Timing remains constant regardless of input
- No information leakage through timing

## Questions

1. Why is the length check still potentially vulnerable?
2. How would you extend this to protect against power analysis?
3. What is the trade-off between security and performance in constant-time implementations?

## Submission

- Python script with both implementations
- Timing analysis plots
- Written answers to questions
"""
,

    "Midterm_Review_Topics.md": """# CYENG350 Midterm Review

## Topics Covered

### Week 1-2: Cryptography Fundamentals
- Symmetric vs asymmetric encryption
- AES, RSA basics
- Hash functions (SHA-256)
- MACs and authenticated encryption

### Week 3-4: Network Security
- TLS/SSL handshake
- Certificate validation
- Common attacks: MITM, replay, downgrade

### Week 5-6: Secure Systems Design
- **Threat modeling** (STRIDE framework) ← High emphasis
- **Secure boot** and chain of trust ← High emphasis
- Trusted execution environments

### Week 7: Side-Channel Attacks
- **Timing attacks** ← Lab 3 material
- Power analysis basics
- Countermeasures (constant-time code)

## Study Strategy

### High-Priority Topics (40% of exam)
1. Threat modeling using STRIDE
2. Secure boot process and attacks
3. Side-channel analysis and mitigations

### Medium-Priority (30% of exam)
1. TLS handshake details
2. Cryptographic primitives (when to use which)
3. Authentication vs encryption

### Lower-Priority (30% of exam)
1. Specific algorithm details
2. Historical context
3. Theoretical proofs

## Practice Problems

### Problem 1: Threat Modeling
Given a system description (e.g., online banking app), identify:
- Assets
- STRIDE threats
- Mitigations for each threat

### Problem 2: Secure Boot
Explain how secure boot prevents:
- Bootkit malware
- Evil maid attacks
- Rollback attacks

### Problem 3: Side-Channels
Why is this code vulnerable, and how would you fix it?

## Common Mistakes to Avoid

1. **Confusing authentication and encryption**
   - Authentication proves identity
   - Encryption protects confidentiality

2. **Misunderstanding threat models**
   - Always define attacker capabilities first
   - "Secure" depends on threat model

3. **Ignoring side-channels**
   - Implementation matters as much as algorithm
   - Timing leaks are real and exploitable

## Formula Sheet (Provided)

You will have access to:
- Common crypto formulas
- Timing complexity notations
- STRIDE definitions
"""
}

ECE347_CONTENT = {
    "Chapter5_Cache_Coherence.md": """# Chapter 5: Cache Coherence in Multiprocessor Systems

## Introduction

In multiprocessor systems, each CPU typically has its own cache. This creates the **cache coherence problem**: multiple copies of the same memory location may exist in different caches, and they may have different values.

## The Cache Coherence Problem

### Example Scenario

```
Initial state: X = 0 in main memory

CPU 0: Read X → X = 0 cached
CPU 1: Read X → X = 0 cached
CPU 0: Write X = 5 → X = 5 in CPU0's cache
```

Now CPU 1's cache still has X = 0 (stale data), while CPU 0 has X = 5.

## Cache Coherence Protocols

### MESI Protocol

MESI is a widely-used cache coherence protocol. Each cache line can be in one of four states:

**M (Modified)**: Line is valid, dirty, and exclusive to this cache
**E (Exclusive)**: Line is valid, clean, and exclusive to this cache
**S (Shared)**: Line is valid and may exist in other caches
**I (Invalid)**: Line is not valid

### State Transitions

**Read Hit**: No state change (stay in M, E, or S)

**Read Miss**:
- If another cache has line in M: → S (writeback first)
- If another cache has line in E or S: → S
- If no other cache has line: → E

**Write Hit**:
- From M: Stay in M
- From E: → M
- From S: → M (invalidate other copies)

**Write Miss**:
- → M (invalidate all other copies)

### Bus Snooping

Each cache monitors (snoops) the bus for transactions involving addresses in its cache.

When CPU 0 writes to X:
1. CPU 0 broadcasts invalidation on bus
2. Other caches see their copy of X and mark it Invalid
3. CPU 0's cache marks X as Modified

## Write Policies

### Write-Through vs Write-Back

**Write-Through**: Every write updates both cache and main memory
- Simpler coherence
- Higher bus traffic

**Write-Back**: Writes only update cache; memory updated when line is evicted
- Lower bus traffic
- More complex coherence (need dirty bit)

## Directory-Based Coherence

For large-scale systems (>16 processors), snooping becomes inefficient.

**Directory**: Centralized structure tracking which caches have which lines

Advantages:
- Reduces broadcast traffic
- Scales better than snooping

Disadvantages:
- Additional latency for directory lookup
- Directory storage overhead

## Performance Considerations

### False Sharing

Two CPUs access different variables that happen to be in the same cache line.

```c
struct {
    int counter_cpu0;  // Used by CPU 0
    int counter_cpu1;  // Used by CPU 1
} shared;  // If in same cache line → ping-pong!
```

**Solution**: Pad structures to ensure variables are in different cache lines.

### True Sharing

Multiple CPUs legitimately access the same variable.

**Mitigation**:
- Use atomic operations
- Minimize critical sections
- Consider per-CPU data structures

## Common Mistakes

1. **Assuming sequential consistency**: Modern CPUs reorder memory operations
2. **Ignoring false sharing**: Can destroy scalability
3. **Over-synchronizing**: Excessive locking creates bottlenecks

## Memory Barriers

**Memory Fence**: Ensures all memory operations before the fence complete before any after it.

Without fences, this can fail:
```c
// CPU 0
data = 42;
ready = 1;

// CPU 1
while (!ready);
print(data);  // Might print 0!
```

With fence:
```c
// CPU 0
data = 42;
memory_fence();
ready = 1;
```
"""
,

    "Lab2_Finite_State_Machines.md": """# Lab 2: Designing Finite State Machines in Verilog

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
"""
,

    "Homework3_Timing_Analysis.md": """# Homework 3: Timing Analysis and Sequential Circuits

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
"""
}


# ============================================================================
# DATA GENERATION
# ============================================================================

def create_test_classes(db):
    """Create 3 test classes."""
    classes = [
        Class(
            code="PHYS214",
            name="Mechanics and Rotational Dynamics",
            status="active"
        ),
        Class(
            code="CYENG350",
            name="Cybersecurity Engineering",
            status="active"
        ),
        Class(
            code="ECE347",
            name="Digital Systems Design",
            status="active"
        )
    ]

    for cls in classes:
        db.add(cls)

    db.commit()

    print(f"[OK] Created {len(classes)} classes")
    return {cls.code: cls for cls in classes}


def create_test_assignments(db, classes):
    """Create 5 assignments per class."""
    assignment_templates = [
        ("HW1", "Homework 1"),
        ("HW2", "Homework 2"),
        ("Lab1", "Laboratory 1"),
        ("Midterm Review", "Midterm Review Materials"),
        ("Final Review", "Final Exam Review")
    ]

    assignments = []
    for class_code, cls in classes.items():
        for code, title in assignment_templates:
            assignment = Assignment(
                class_id=cls.id,
                title=f"{code}: {title}",
                due_date=datetime.utcnow() + timedelta(days=7),
                status="todo"
            )
            db.add(assignment)
            assignments.append((class_code, assignment))

    db.commit()
    print(f"[OK] Created {len(assignments)} assignments")
    return assignments


def create_artifacts_and_extract(db, assignments, class_content):
    """Create artifacts from synthetic content."""
    artifacts_created = 0

    for class_code, assignment in assignments:
        content_dict = class_content.get(class_code, {})

        for filename, content in content_dict.items():
            # Save to vault
            safe_filename = f"{class_code}_{assignment.id}_{filename}"
            file_path = VAULT_PATH / safe_filename

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Calculate hash
            file_hash = hashlib.sha256(content.encode()).hexdigest()

            # Create artifact
            artifact = Artifact(
                assignment_id=assignment.id,
                filename=safe_filename,
                original_filename=filename,
                file_path=str(file_path),
                file_type='markdown',
                file_size=len(content),
                file_hash=file_hash
            )
            db.add(artifact)
            db.flush()  # Get artifact.id

            # Create extracted text (content is already text)
            extracted = ExtractedText(
                artifact_id=artifact.id,
                content=content,
                extraction_method='plain',
                extraction_status='success'
            )
            db.add(extracted)

            artifacts_created += 1

    db.commit()
    print(f"[OK] Created {artifacts_created} artifacts with extracted text")


def chunk_all_content(db):
    """Run chunking service on all extracted texts."""
    chunking_service = ChunkingService()
    count = chunking_service.chunk_all_extracted_texts(db, force_rechunk=True)
    print(f"[OK] Chunked {count} extracted texts")


def generate_test_queries():
    """Generate test queries mapped to expected classes."""
    queries = {
        "PHYS214": [
            "rotational dynamics",
            "moment of inertia",
            "torque calculation",
            "angular momentum conservation",
            "rotational kinetic energy"
        ],
        "CYENG350": [
            "threat model",
            "secure boot",
            "side channel attack",
            "timing attack mitigation",
            "STRIDE framework"
        ],
        "ECE347": [
            "cache coherence",
            "finite state machine",
            "setup time hold time",
            "MESI protocol",
            "metastability"
        ]
    }

    # Save to file
    output_path = Path(__file__).parent / "test_queries.json"
    with open(output_path, 'w') as f:
        json.dump(queries, f, indent=2)

    print(f"[OK] Generated test queries -> {output_path}")
    return queries


def run_test_queries(db, test_queries):
    """Run test queries and print results."""
    from marcus_app.services.search_service import SearchService

    search_service = SearchService()

    print("\n" + "="*70)
    print("SEARCH TEST RESULTS")
    print("="*70 + "\n")

    for class_code, queries in test_queries.items():
        print(f"\n{class_code} Queries:")
        print("-" * 70)

        # Get class_id
        cls = db.query(Class).filter(Class.code == class_code).first()
        if not cls:
            print(f"  ERROR: Class {class_code} not found")
            continue

        for query in queries:
            results = search_service.search(
                query=query,
                class_id=cls.id,
                limit=3,
                db=db
            )

            print(f"\nQuery: '{query}'")
            if not results:
                print("  [WARNING] No results found")
            else:
                for i, result in enumerate(results, 1):
                    score = int(result['score'] * 100)
                    snippet = result['snippet'][:80] + "..." if len(result['snippet']) > 80 else result['snippet']
                    # Encode to ASCII-safe version
                    snippet_safe = snippet.encode('ascii', errors='replace').decode('ascii')
                    print(f"  {i}. [{score}%] {result['artifact_filename']}")
                    print(f"     Chunk {result['chunk_id']} | {result['search_method']}")
                    print(f"     \"{snippet_safe}\"")


def main():
    """Main execution."""
    print("\n" + "="*70)
    print("Marcus v0.3 Test Data Loader")
    print("="*70 + "\n")

    # Initialize DB
    init_db()
    db = SessionLocal()

    try:
        # Check if test artifacts already exist
        existing_chunks = db.query(TextChunk).count()
        if existing_chunks > 0:
            print(f"\n[WARNING] Test data already exists ({existing_chunks} chunks found).")
            print("Running search tests only...\n")

            # Skip to test queries
            test_queries = generate_test_queries()
            run_test_queries(db, test_queries)

            print("\n" + "="*70)
            print("[OK] Search tests completed!")
            print("="*70)
            db.close()
            return

        # Create or reuse classes
        existing_class = db.query(Class).filter(Class.code == "PHYS214").first()
        if existing_class:
            print("\n[INFO] Using existing classes")
            classes = {cls.code: cls for cls in db.query(Class).filter(
                Class.code.in_(["PHYS214", "CYENG350", "ECE347"])
            ).all()}
        else:
            classes = create_test_classes(db)
        assignments = create_test_assignments(db, classes)

        # Map content to classes
        class_content = {
            "PHYS214": PHYS214_CONTENT,
            "CYENG350": CYENG350_CONTENT,
            "ECE347": ECE347_CONTENT
        }

        create_artifacts_and_extract(db, assignments, class_content)
        chunk_all_content(db)

        # Generate and run test queries
        test_queries = generate_test_queries()
        run_test_queries(db, test_queries)

        print("\n" + "="*70)
        print("[OK] Test data loaded successfully!")
        print("="*70)
        print("\nNext steps:")
        print("1. Start server: python main.py")
        print("2. Open: http://localhost:8000/static/search.html")
        print("3. Try searching: 'rotational dynamics', 'cache coherence', 'threat model'")
        print("4. Verify citations and context viewer work")

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
