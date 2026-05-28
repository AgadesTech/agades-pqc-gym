import Mathlib.Data.Nat.Basic

namespace AgadesPQC

structure MultivariateTarget where
  variables : Nat
  equations : Nat
  hasField : Bool

namespace Multivariate
namespace Target

def VariablesEquationsFieldPresent (target : MultivariateTarget) : Prop :=
  target.variables > 0 ∧ target.equations > 0 ∧ target.hasField = true

theorem variables_equations_field_present
    (target : MultivariateTarget)
    (hvariables : target.variables > 0)
    (hequations : target.equations > 0)
    (hfield : target.hasField = true) :
    VariablesEquationsFieldPresent target := by
  exact And.intro hvariables (And.intro hequations hfield)

def ApplicabilityShape (target : MultivariateTarget) : Prop :=
  VariablesEquationsFieldPresent target

theorem applicability_shape
    (target : MultivariateTarget)
    (hshape : VariablesEquationsFieldPresent target) :
    ApplicabilityShape target := by
  exact hshape

end Target
end Multivariate
end AgadesPQC
