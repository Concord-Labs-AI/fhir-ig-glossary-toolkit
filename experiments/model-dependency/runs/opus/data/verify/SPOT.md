# Verification packet SPOT — spot check of unmatched findings

7 findings — one verdict per key.

## `input/pagecontent/connecting_applications_with_api_data_sources.md@3311`

- File: `input/pagecontent/connecting_applications_with_api_data_sources.md` line 28 (Prose, paragraph)
- Type / terms / confidence: Misuse / T-PROV, T-HCO / Medium
- Decision: D-8 (recommended: change)
- Issue: The referral source is an organization, but the glossary defines a provider as a person; the organization example is a health care organization.
- Find: `Provider`
- Replace: `health care organization`
- Context: FHIR-enabled CBO Applications follow the [Direct Referral Light] or [Indirect Referral Light] use cases. This section describes the initial connection of the FHIR-enabled CBO application to the referral source (Provider or Coordination Platform system).

## `input/pagecontent/connecting_applications_with_api_data_sources.md@808`

- File: `input/pagecontent/connecting_applications_with_api_data_sources.md` line 9 (Prose, heading)
- Type / terms / confidence: Missed use / T-PAT / High
- Decision: D-2 (recommended: change)
- Issue: 'Client' here means the person, whom the glossary calls 'patient'; 'client' also names software in this guide, so D-2's recommended option drops it for people.
- Find: `Patient/Client`
- Replace: `Patient`
- Context: #### Patient/Client Applications

## `input/pagecontent/enrollment.md@3599`

- File: `input/pagecontent/enrollment.md` line 54 (Prose, list-item)
- Type / terms / confidence: Misuse / T-PROV, T-RS / Medium
- Decision: D-8 (recommended: change)
- Issue: Sending a ServiceRequest and Task is a system action, but the glossary defines a provider as a person; the referral source's system sends them.
- Find: `sends a referral via`
- Replace: `initiates a referral, which the referral source's system sends via`
- Context: 1. Assessment and Referral: A provider assesses a patient, identifies an HRSN, and sends a referral via a ServiceRequest and Task.


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


## `input/fsh/instances/SDOHCC-ReferralSource.fsh@836`

- File: `input/fsh/instances/SDOHCC-ReferralSource.fsh` line 12 (Artifact text, purpose)
- Type / terms / confidence: Missed use / T-RT / Medium
- Decision: —
- Issue: 'Recipients of requests for service' describes the role the glossary calls 'referral target'.
- Find: `recipients of requests for service`
- Replace: `referral targets`
- Context: Because systems that originate requests for service may sometimes also be recipients of requests for service, the requirements include 'SHOULD' expectations to also accept and process requests from other systems. The referral source may either interact directly with a [Referral Recipient](CapabilityStatement-SDOHCC-ReferralRecipient.html) or will interact through a [Coordination Platform](CapabilityStatement-SDOHCC-CoordinationPlatform.html) operated by an intermediary. Responsibilities of Referral Sources include capturing information from a patient in the form of QuestionnaireResponses, Obse

## `input/fsh/instances/SDOHCC-ReferralSource.fsh@94147`

- File: `input/fsh/instances/SDOHCC-ReferralSource.fsh` line 968 (Artifact text, rest[=].documentation)
- Type / terms / confidence: Missed use / T-RT / High
- Decision: —
- Issue: Bare 'recipient' stands for the referral target named in the same sentence; the glossary term is 'referral target'.
- Find: `where the recipient is`
- Replace: `where the referral target is`
- Context: Referral sources must make both the referral and all information referenced by it available to downstream [coordination platforms](CapabilityStatement-SDOHCC-CoordinationPlatform.html) and [referral recipient](CapabilityStatement-SDOHCC-ReferralRecipient.html) systems and - depending on the capabilities of the receivers - may also need to make the Tasks themselves available for query and support writing of procedures in situations where the recipient is a ['light' referral recipient](CapabilityStatement-SDOHCC-ReferralRecipient.html) that doesn't have local persistence or FHIR server capabilit

