# Chapter 5: Cache Coherence in Multiprocessor Systems

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
