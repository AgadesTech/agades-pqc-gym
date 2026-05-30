import Lake
open Lake DSL

package agades_pqc_formal where
  -- Lean 4 + Mathlib backend for Agades PQC Gym proof artifacts.

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "v4.12.0"

lean_lib AgadesPQC where
  srcDir := "."
