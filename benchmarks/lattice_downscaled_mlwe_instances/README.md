# Lattice Downscaled MLWE Instances

This directory contains tiny public MLWE-style fixtures for deterministic
adapter reproduction tests.

The fixtures linearize a small module secret into coefficient rows so the public
verifier can perform bounded exhaustive search without implementing a full
polynomial-ring attack stack. They are deliberately small, public, and marked as
non-claims; they only prove that the lattice adapter can connect an MLWE
`AttackPlan` to a public downscaled reproduction harness.
