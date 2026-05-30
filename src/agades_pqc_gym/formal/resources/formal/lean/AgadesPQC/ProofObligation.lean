namespace AgadesPQC
namespace ProofObligation

inductive ObligationKind where
  | targetInvariant
  | operatorPrecondition
  | schemaOnlyBoundary
  | familyApplicabilityBoundary
  | estimatorClaimBoundary
  deriving DecidableEq

inductive ObligationScope where
  | target
  | operator
  | schemaOnlyEstimatorBoundary
  | familyApplicability
  | estimator
  deriving DecidableEq

structure ObligationTypeRule where
  kind : ObligationKind
  scope : ObligationScope
  reviewRequiredBeforeClaim : Bool
  securityClaimAllowed : Bool

def ScopeForKind (kind : ObligationKind) (scope : ObligationScope) : Prop :=
  match kind, scope with
  | ObligationKind.targetInvariant, ObligationScope.target => True
  | ObligationKind.operatorPrecondition, ObligationScope.operator => True
  | ObligationKind.schemaOnlyBoundary,
    ObligationScope.schemaOnlyEstimatorBoundary => True
  | ObligationKind.familyApplicabilityBoundary,
    ObligationScope.familyApplicability => True
  | ObligationKind.estimatorClaimBoundary, ObligationScope.estimator => True
  | _, _ => False

def WellTyped (rule : ObligationTypeRule) : Prop :=
  ScopeForKind rule.kind rule.scope ∧
    rule.reviewRequiredBeforeClaim = true ∧
    rule.securityClaimAllowed = false

def TargetInvariantRule : ObligationTypeRule where
  kind := ObligationKind.targetInvariant
  scope := ObligationScope.target
  reviewRequiredBeforeClaim := true
  securityClaimAllowed := false

def OperatorPreconditionRule : ObligationTypeRule where
  kind := ObligationKind.operatorPrecondition
  scope := ObligationScope.operator
  reviewRequiredBeforeClaim := true
  securityClaimAllowed := false

def SchemaOnlyBoundaryRule : ObligationTypeRule where
  kind := ObligationKind.schemaOnlyBoundary
  scope := ObligationScope.schemaOnlyEstimatorBoundary
  reviewRequiredBeforeClaim := true
  securityClaimAllowed := false

def FamilyApplicabilityBoundaryRule : ObligationTypeRule where
  kind := ObligationKind.familyApplicabilityBoundary
  scope := ObligationScope.familyApplicability
  reviewRequiredBeforeClaim := true
  securityClaimAllowed := false

def EstimatorClaimBoundaryRule : ObligationTypeRule where
  kind := ObligationKind.estimatorClaimBoundary
  scope := ObligationScope.estimator
  reviewRequiredBeforeClaim := true
  securityClaimAllowed := false

def ReviewedBeforeSecurityClaim
    (reviewed : Bool)
    (securityClaimAllowed : Bool) : Prop :=
  reviewed = true ∨ securityClaimAllowed = false

theorem target_invariant_typed :
    WellTyped TargetInvariantRule := by
  unfold TargetInvariantRule WellTyped ScopeForKind
  simp

theorem operator_precondition_typed :
    WellTyped OperatorPreconditionRule := by
  unfold OperatorPreconditionRule WellTyped ScopeForKind
  simp

theorem schema_only_boundary_typed :
    WellTyped SchemaOnlyBoundaryRule := by
  unfold SchemaOnlyBoundaryRule WellTyped ScopeForKind
  simp

theorem family_applicability_boundary_typed :
    WellTyped FamilyApplicabilityBoundaryRule := by
  unfold FamilyApplicabilityBoundaryRule WellTyped ScopeForKind
  simp

theorem estimator_claim_boundary_typed :
    WellTyped EstimatorClaimBoundaryRule := by
  unfold EstimatorClaimBoundaryRule WellTyped ScopeForKind
  simp

theorem unreviewed_obligation_blocks_security_claim :
    ReviewedBeforeSecurityClaim false false := by
  unfold ReviewedBeforeSecurityClaim
  exact Or.inr rfl

end ProofObligation
end AgadesPQC
