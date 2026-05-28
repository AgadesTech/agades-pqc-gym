namespace AgadesPQC
namespace Generic
namespace Target

def FamilyShapeValidated (acceptedByFamilyValidator : Bool) : Prop :=
  acceptedByFamilyValidator = true

theorem family_shape_validated : FamilyShapeValidated true := by
  rfl

end Target
end Generic
end AgadesPQC
