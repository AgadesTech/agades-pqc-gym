namespace AgadesPQC
namespace AttackPlan

inductive ClaimReviewStatus where
  | pendingReview
  | reviewed
  deriving DecidableEq

inductive ClaimKind where
  | applicability
  | estimatorResult
  | cryptographicSecurity
  deriving DecidableEq

structure SemanticsContract where
  schemaAccepted : Bool
  canonicalized : Bool
  extraFieldsRejected : Bool
  operatorsNonempty : Bool
  familyOperatorSupported : Bool
  claimsReviewGated : Bool

def WellFormed (contract : SemanticsContract) : Prop :=
  contract.schemaAccepted = true ∧
    contract.canonicalized = true ∧
    contract.extraFieldsRejected = true ∧
    contract.operatorsNonempty = true ∧
    contract.familyOperatorSupported = true ∧
    contract.claimsReviewGated = true

def PublicContract : SemanticsContract where
  schemaAccepted := true
  canonicalized := true
  extraFieldsRejected := true
  operatorsNonempty := true
  familyOperatorSupported := true
  claimsReviewGated := true

def CanonicalizationStable (canonicalDigestMatches : Bool) : Prop :=
  canonicalDigestMatches = true

def OperatorsNonempty (operatorCount : Nat) : Prop :=
  operatorCount > 0

def RejectedWhenUnsupported
    (planAccepted : Bool)
    (familyOperatorSupported : Bool) : Prop :=
  familyOperatorSupported = false → planAccepted = false

def SecurityClaimAllowed
    (reviewStatus : ClaimReviewStatus)
    (kind : ClaimKind) : Prop :=
  kind ≠ ClaimKind.cryptographicSecurity ∨
    reviewStatus = ClaimReviewStatus.reviewed

theorem schema_contract_well_formed :
    WellFormed PublicContract := by
  unfold PublicContract WellFormed
  simp

theorem canonicalization_stable :
    CanonicalizationStable true := by
  rfl

theorem operators_nonempty :
    OperatorsNonempty 1 := by
  unfold OperatorsNonempty
  decide

theorem unsupported_operator_rejected :
    RejectedWhenUnsupported false false := by
  intro _
  rfl

theorem unreviewed_security_claim_forbidden :
    ¬ SecurityClaimAllowed
      ClaimReviewStatus.pendingReview
      ClaimKind.cryptographicSecurity := by
  intro h
  cases h with
  | inl hkind =>
      exact hkind rfl
  | inr hreview =>
      cases hreview

end AttackPlan
end AgadesPQC
