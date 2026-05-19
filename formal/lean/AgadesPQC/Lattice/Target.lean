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

end Target
end Lattice
end AgadesPQC
