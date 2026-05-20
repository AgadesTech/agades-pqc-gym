import Mathlib.Data.Nat.Basic

namespace AgadesPQC
namespace Lattice
namespace PrimalUSVP

def BetaValidRange (beta targetDimension : Nat) : Prop :=
  beta > 0 ∧ beta ≤ targetDimension

theorem beta_valid_range
    (beta targetDimension : Nat)
    (hpositive : beta > 0)
    (hbounded : beta ≤ targetDimension) :
    BetaValidRange beta targetDimension := by
  exact And.intro hpositive hbounded

end PrimalUSVP
end Lattice
end AgadesPQC
