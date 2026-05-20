# Lattice Downscaled LWE Instances

This directory contains deliberately tiny public LWE fixtures for bounded
reproduction plumbing. The fixtures are small enough for exhaustive search and
exist only to verify that the family adapter can connect an `AttackPlan` to an
actual public instance-solving harness.

The current set includes tiny binary-secret and ternary-secret fixtures so the
adapter exercises more than one public secret domain.

These fixtures are not security claims, not ML-KEM evidence, and not private
evolution traces.
