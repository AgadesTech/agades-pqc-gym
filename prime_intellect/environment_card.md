# Environment Card: Agades LWE Strategy Gym

## Environment

An agent submits AttackPlan JSON and receives validation, estimator, and fitness metrics.

## Observation

Target parameters, allowed operators, constraints, assumptions, and prior public toy results.

## Action

Submit a modified AttackPlan JSON file. The MVP does not execute arbitrary Python candidates.

## Reward

`combined_score`, with penalties for invalidity, memory/time violations, unstable assumptions, and unreproducibility.

## Safety

Only toy, downscaled, and public benchmark targets are allowed.

