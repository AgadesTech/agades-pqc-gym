namespace AgadesPQC
namespace Evaluator

inductive ClaimStatus where
  | noSecurityClaim
  | reviewedSecurityClaim
  deriving DecidableEq

def NoSecurityClaim (status : ClaimStatus) : Prop :=
  status = ClaimStatus.noSecurityClaim

theorem no_security_claim : NoSecurityClaim ClaimStatus.noSecurityClaim := by
  rfl

end Evaluator
end AgadesPQC
