# Lecture 7: Threat Modeling and Security Analysis

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
