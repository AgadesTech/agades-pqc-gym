namespace AgadesPQC
namespace OperatorSemantics

inductive ClaimReviewStatus where
  | unreviewed
  | reviewed
  deriving DecidableEq

inductive ClaimKind where
  | applicability
  | routing
  | cryptographicSecurity
  deriving DecidableEq

def RequiredParameterBound (hasAllRequiredParams : Bool) : Prop :=
  hasAllRequiredParams = true

def FamilyBindingValid (isBoundToFamily : Bool) : Prop :=
  isBoundToFamily = true

def SecurityClaimAllowed
    (reviewStatus : ClaimReviewStatus)
    (kind : ClaimKind) : Prop :=
  kind ≠ ClaimKind.cryptographicSecurity ∨
    reviewStatus = ClaimReviewStatus.reviewed

theorem required_parameter_bound :
    RequiredParameterBound true := by
  rfl

theorem family_binding_valid :
    FamilyBindingValid true := by
  rfl

theorem unreviewed_security_claim_forbidden :
    ¬ SecurityClaimAllowed
      ClaimReviewStatus.unreviewed
      ClaimKind.cryptographicSecurity := by
  intro h
  cases h with
  | inl hkind =>
      exact hkind rfl
  | inr hreview =>
      cases hreview

end OperatorSemantics
end AgadesPQC
