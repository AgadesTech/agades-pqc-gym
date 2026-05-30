namespace AgadesPQC
namespace CodeBased
namespace SchemaOnly

def NoEstimate (emitsEstimate : Bool) : Prop :=
  emitsEstimate = false

theorem no_estimate : NoEstimate false := by
  rfl

end SchemaOnly
end CodeBased
end AgadesPQC
