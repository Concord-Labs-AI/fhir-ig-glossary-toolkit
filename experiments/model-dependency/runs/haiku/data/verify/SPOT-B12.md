# Verification packet SPOT-B12

4 findings — one verdict per key.

## `input/fsh/instances/SDOHCC-ReferralSource.fsh@171550`

- File: `input/fsh/instances/SDOHCC-ReferralSource.fsh` line 1771 (Artifact text, rest[=].resource[=].searchParam[=].documentation)
- Type / terms / confidence: Missed use / T-PAT / Medium
- Decision: D-2 (recommended: keep)
- Issue: Strict glossary wording is 'patient', but the author of a QuestionnaireResponse may be a caregiver or representative rather than the patient, so the recommended option keeps 'individual' here.
- Find: `particular individual`
- Replace: `particular patient`
- Context: Allows filtering QuestionnaireResponses previously created/edited by a particular individual

## `input/fsh/instances/SDOHCC-ReferralSource.fsh@68797`

- File: `input/fsh/instances/SDOHCC-ReferralSource.fsh` line 710 (Artifact text, rest[=].resource[=].searchParam[=].documentation)
- Type / terms / confidence: Missed use / T-PAT / Medium
- Decision: D-2 (recommended: keep)
- Issue: Strict glossary wording is 'patient', but the author of a QuestionnaireResponse may be a caregiver or representative rather than the patient, so the recommended option keeps 'individual' here.
- Find: `particular individual`
- Replace: `particular patient`
- Context: Allows filtering QuestionnaireResponses previously created/edited by a particular individual

## `input/fsh/instances/SDOHCC-ReferralSource.fsh@836`

- File: `input/fsh/instances/SDOHCC-ReferralSource.fsh` line 12 (Artifact text, purpose)
- Type / terms / confidence: Missed use / T-RT / Medium
- Decision: —
- Issue: Systems that receive requests for service are referral targets in the glossary; 'recipients' is the bare name the glossary does not use.
- Find: `recipients of requests for service`
- Replace: `referral targets for requests for service`
- Context: Because systems that originate requests for service may sometimes also be recipients of requests for service, the requirements include 'SHOULD' expectations to also accept and process requests from other systems. The referral source may either interact directly with a [Referral Recipient](CapabilityStatement-SDOHCC-ReferralRecipient.html) or will interact through a [Coordination Platform](CapabilityStatement-SDOHCC-CoordinationPlatform.html) operated by an intermediary. Responsibilities of Referral Sources include capturing information from a patient in the form of QuestionnaireResponses, Obse

## `input/fsh/instances/SDOHCC-ReferralSource.fsh@94153`

- File: `input/fsh/instances/SDOHCC-ReferralSource.fsh` line 968 (Artifact text, rest[=].documentation)
- Type / terms / confidence: Missed use / T-RT / High
- Decision: —
- Issue: Bare 'recipient' stands for the referral target in this sentence.
- Find: `the recipient is`
- Replace: `the referral target is`
- Context: Referral sources must make both the referral and all information referenced by it available to downstream [coordination platforms](CapabilityStatement-SDOHCC-CoordinationPlatform.html) and [referral recipient](CapabilityStatement-SDOHCC-ReferralRecipient.html) systems and - depending on the capabilities of the receivers - may also need to make the Tasks themselves available for query and support writing of procedures in situations where the recipient is a ['light' referral recipient](CapabilityStatement-SDOHCC-ReferralRecipient.html) that doesn't have local persistence or FHIR server capabilit
