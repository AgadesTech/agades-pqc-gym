import Mathlib.Data.Nat.Basic

namespace AgadesPQC

structure LatticeTarget where
  n : Nat
  q : Nat
  hasSecretDistribution : Bool
  hasErrorDistribution : Bool

namespace Lattice
namespace Target

def DimensionModulusPositive (target : LatticeTarget) : Prop :=
  target.n > 0 ∧ target.q > 1

theorem dimension_modulus_positive
    (target : LatticeTarget)
    (hn : target.n > 0)
    (hq : target.q > 1) :
    DimensionModulusPositive target := by
  exact And.intro hn hq

def DistributionsPresent (target : LatticeTarget) : Prop :=
  target.hasSecretDistribution = true ∧ target.hasErrorDistribution = true

theorem distributions_present
    (target : LatticeTarget)
    (hsecret : target.hasSecretDistribution = true)
    (herror : target.hasErrorDistribution = true) :
    DistributionsPresent target := by
  exact And.intro hsecret herror

def ParametersPositive (target : LatticeTarget) : Prop :=
  target.n > 0 ∧ target.q > 1

theorem parameters_positive
    (target : LatticeTarget)
    (hn : target.n > 0)
    (hq : target.q > 1) :
    ParametersPositive target := by
  exact And.intro hn hq

def ModuleRankPresent (k : Nat) : Prop :=
  k > 0

theorem module_rank_present
    (k : Nat)
    (hk : k > 0) :
    ModuleRankPresent k := by
  exact hk

def NTRUSchemaShape (target : LatticeTarget) : Prop :=
  target.n > 0 ∧ target.q > 1 ∧ target.hasSecretDistribution = true

theorem ntru_schema_shape
    (target : LatticeTarget)
    (hn : target.n > 0)
    (hq : target.q > 1)
    (hsecret : target.hasSecretDistribution = true) :
    NTRUSchemaShape target := by
  exact And.intro hn (And.intro hq hsecret)

def SISSchemaShape (target : LatticeTarget) : Prop :=
  target.n > 0 ∧ target.q > 1 ∧ target.hasSecretDistribution = true

theorem sis_schema_shape
    (target : LatticeTarget)
    (hn : target.n > 0)
    (hq : target.q > 1)
    (hsecret : target.hasSecretDistribution = true) :
    SISSchemaShape target := by
  exact And.intro hn (And.intro hq hsecret)

def SchemaOnlyNoEstimate : Prop :=
  True

theorem ntru_schema_only_no_estimate :
    SchemaOnlyNoEstimate := by
  exact True.intro

theorem sis_schema_only_no_estimate :
    SchemaOnlyNoEstimate := by
  exact True.intro

end Target
end Lattice
end AgadesPQC
