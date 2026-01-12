# CYENG350 Midterm Review

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
