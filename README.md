<!-- @format -->

# Agentic Development Essay — Case Study Repository

This repository accompanies the essay:

**Agentic Development Is a New Production Mode**  
https://heterodoxity.substack.com/p/agentic-development-production-mode

It contains the case study artifacts used to examine how agentic systems behave under different levels of specification and design constraint.

## Repository Structure

The `main` branch contains only this README.  
All experimental work lives in separate branches.

### Branches

- **mini_spec**  
  Minimal upfront specification and design.  
  The agent was given only a high-level contract and allowed to choose structure and assumptions.

- **full_spec**  
  Explicit specification, design artifacts, constraints, and validation expectations.  
  The agent was bound to these documents as authoritative inputs.

Each branch is a complete, runnable version of the same system built under different control surfaces.

## How to Use

To explore a run:

```bash
git checkout mini_spec
# or
git checkout full_spec
```

Follow the instructions in the branch to build and run the system.

Comparing the two branches shows how agent behavior, architecture, drift, and convergence change as intent and constraint are made explicit.

## Purpose

This repository is not a product.
It is a controlled experiment supporting the essay’s argument about:

- Specification and design as control surfaces.
- Left-shifted governance in agentic development.
- Why agentic performance degrades with system scale.
- How explicit intent affects convergence.

The code is provided for inspection, reproduction, and critique.

## License

MIT — experimental and educational use only.
