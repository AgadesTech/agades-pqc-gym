namespace AgadesPQC
namespace EstimatorModel

inductive EstimatorSupport where
  | schemaOnlyNoEstimator
  | runtimeEstimator
  deriving DecidableEq

inductive ResultBinding where
  | notBound
  | boundToProofArtifact
  deriving DecidableEq

def OperatorCompatibilityDeclared (compatible : Bool) : Prop :=
  compatible = true

def ResultBindingRequiredBeforeClaim
    (support : EstimatorSupport)
    (binding : ResultBinding) : Prop :=
  support = EstimatorSupport.schemaOnlyNoEstimator ∨
    binding = ResultBinding.boundToProofArtifact

def SchemaOnlyNoEstimator (support : EstimatorSupport) : Prop :=
  support = EstimatorSupport.schemaOnlyNoEstimator

theorem operator_compatibility_declared :
    OperatorCompatibilityDeclared true := by
  rfl

theorem result_binding_required_before_claim :
    ResultBindingRequiredBeforeClaim
      EstimatorSupport.runtimeEstimator
      ResultBinding.boundToProofArtifact := by
  exact Or.inr rfl

theorem schema_only_no_estimator :
    SchemaOnlyNoEstimator EstimatorSupport.schemaOnlyNoEstimator := by
  rfl

end EstimatorModel
end AgadesPQC
