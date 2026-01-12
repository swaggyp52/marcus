# Lab 3: Side-Channel Analysis

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
