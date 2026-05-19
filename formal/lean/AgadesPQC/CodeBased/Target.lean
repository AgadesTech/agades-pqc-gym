import Mathlib.Data.Nat.Basic

namespace AgadesPQC

structure CodeBasedTarget where
  n : Nat
  k : Nat
  w : Nat

namespace CodeBased
namespace Target

def ParametersWellFormed (target : CodeBasedTarget) : Prop :=
  target.n > 0 ∧ target.k > 0 ∧ target.w > 0 ∧ target.k ≤ target.n

theorem parameters_well_formed
    (target : CodeBasedTarget)
    (hn : target.n > 0)
    (hk : target.k > 0)
    (hw : target.w > 0)
    (hkBound : target.k ≤ target.n) :
    ParametersWellFormed target := by
  exact And.intro hn (And.intro hk (And.intro hw hkBound))

end Target
end CodeBased
end AgadesPQC
