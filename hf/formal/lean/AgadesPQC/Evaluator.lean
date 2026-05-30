namespace AgadesPQC
namespace Evaluator

inductive ClaimStatus where
  | noSecurityClaim
  | reviewedSecurityClaim
  deriving DecidableEq

inductive EstimatorBindingStatus where
  | notAttached
  | attachedUnreviewed
  | schemaOnlyNoEstimator
  | reviewed
  deriving DecidableEq

def NoSecurityClaim (status : ClaimStatus) : Prop :=
  status = ClaimStatus.noSecurityClaim

def BindingHasNoSecurityClaim (status : EstimatorBindingStatus) : Prop :=
  status = EstimatorBindingStatus.notAttached ∨
  status = EstimatorBindingStatus.attachedUnreviewed ∨
  status = EstimatorBindingStatus.schemaOnlyNoEstimator

theorem no_security_claim : NoSecurityClaim ClaimStatus.noSecurityClaim := by
  rfl

theorem attached_unreviewed_no_security_claim :
    BindingHasNoSecurityClaim EstimatorBindingStatus.attachedUnreviewed := by
  exact Or.inr (Or.inl rfl)

theorem schema_only_no_estimator_no_security_claim :
    BindingHasNoSecurityClaim EstimatorBindingStatus.schemaOnlyNoEstimator := by
  exact Or.inr (Or.inr rfl)

end Evaluator
end AgadesPQC
