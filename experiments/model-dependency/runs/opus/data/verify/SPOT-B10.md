# Verification packet SPOT-B10

2 findings — one verdict per key.

## `input/images-source/DetailedIndirectReferral.plantuml@1877`

- File: `input/images-source/DetailedIndirectReferral.plantuml` line 31 (Diagram, diagram line)
- Type / terms / confidence: Form / T-CP / High
- Decision: —
- Issue: The coordination platform's acronym is run into 'Task'; every other line in this diagram writes 'CP Task'.
- Find: `CPTask`
- Replace: `CP Task`
- Context: C -> C : Complete Service\nCreate [[StructureDefinition-SDOHCC-Procedure.html SDOHCC Procedure(s)]](s)\nUpdate CPTask Status to Completed

## `input/images-source/SelfReferralWorkflow.plantuml@105`

- File: `input/images-source/SelfReferralWorkflow.plantuml` line 5 (Diagram, diagram line)
- Type / terms / confidence: Misuse / T-RS, T-CP / Medium
- Decision: —
- Issue: The glossary makes the self-referral referral source the organization running the community resource referral platform (the coordination platform), not the person; this actor creates, posts and polls Tasks, so it is the platform the individual uses.
- Find: `Actor:`
- Replace: `Actor: Coordination Platform used by`
- Context: participant "Role: Referral Source\nActor: Individual or Authorized Individual" as A
