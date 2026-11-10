# Verification packet SPOT-B12

6 findings — one verdict per key.

## `input/fsh/instances/SDOHCC-ReferralSource.fsh@171550`

- File: `input/fsh/instances/SDOHCC-ReferralSource.fsh` line 1771 (Artifact text, rest[=].resource[=].searchParam[=].documentation)
- Type / terms / confidence: Missed use / T-PAT / Medium
- Decision: D-2 (recommended: keep)
- Issue: Strict glossary reading makes 'individual' a missed use of 'patient', but here the person may be a practitioner, so the wording is kept under the recommended option.
- Find: `particular individual`
- Replace: `particular patient`
- Context: Allows filtering QuestionnaireResponses previously created/edited by a particular individual

## `input/fsh/instances/SDOHCC-ReferralSource.fsh@196113`

- File: `input/fsh/instances/SDOHCC-ReferralSource.fsh` line 2017 (Artifact text, rest[=].resource[=].searchParam[=].documentation)
- Type / terms / confidence: Missed use / T-PAT / Medium
- Decision: D-2 (recommended: keep)
- Issue: Strict glossary reading makes 'individual' a missed use of 'patient', but here the person may be a practitioner, so the wording is kept under the recommended option.
- Find: `organization or individual`
- Replace: `organization or patient`
- Context: Allows retrieving all tasks that have been requested by a particular organization or individual. This will commonly be used to monitor the tasks initiated by a particular system

## `input/fsh/instances/SDOHCC-ReferralSource.fsh@68797`

- File: `input/fsh/instances/SDOHCC-ReferralSource.fsh` line 710 (Artifact text, rest[=].resource[=].searchParam[=].documentation)
- Type / terms / confidence: Missed use / T-PAT / Medium
- Decision: D-2 (recommended: keep)
- Issue: Strict glossary reading makes 'individual' a missed use of 'patient', but here the person may be a practitioner, so the wording is kept under the recommended option.
- Find: `particular individual`
- Replace: `particular patient`
- Context: Allows filtering QuestionnaireResponses previously created/edited by a particular individual

## `input/fsh/instances/SDOHCC-ReferralSource.fsh@836`

- File: `input/fsh/instances/SDOHCC-ReferralSource.fsh` line 12 (Artifact text, purpose)
- Type / terms / confidence: Missed use / T-RT / Medium
- Decision: —
- Issue: Bare 'recipients of requests for service' describes the glossary role 'referral target'.
- Find: `recipients of requests for service`
- Replace: `referral targets`
- Context: Because systems that originate requests for service may sometimes also be recipients of requests for service, the requirements include 'SHOULD' expectations to also accept and process requests from other systems. The referral source may either interact directly with a [Referral Recipient](CapabilityStatement-SDOHCC-ReferralRecipient.html) or will interact through a [Coordination Platform](CapabilityStatement-SDOHCC-CoordinationPlatform.html) operated by an intermediary. Responsibilities of Referral Sources include capturing information from a patient in the form of QuestionnaireResponses, Obse

## `input/fsh/instances/SDOHCC-ReferralSource.fsh@91642`

- File: `input/fsh/instances/SDOHCC-ReferralSource.fsh` line 944 (Artifact text, rest[=].resource[=].searchParam[=].documentation)
- Type / terms / confidence: Missed use / T-PAT / Medium
- Decision: D-2 (recommended: keep)
- Issue: Strict glossary reading makes 'individual' a missed use of 'patient', but here the person may be a practitioner, so the wording is kept under the recommended option.
- Find: `organization or individual`
- Replace: `organization or patient`
- Context: Allows retrieving all tasks that have been requested by a particular organization or individual. This will commonly be used to monitor the tasks initiated by a particular system

## `input/fsh/instances/SDOHCC-ReferralSource.fsh@94153`

- File: `input/fsh/instances/SDOHCC-ReferralSource.fsh` line 968 (Artifact text, rest[=].documentation)
- Type / terms / confidence: Missed use / T-RT / Medium
- Decision: —
- Issue: Bare 'recipient' stands for the referral target named earlier in the sentence.
- Find: `the recipient is a`
- Replace: `the referral target is a`
- Context: Referral sources must make both the referral and all information referenced by it available to downstream [coordination platforms](CapabilityStatement-SDOHCC-CoordinationPlatform.html) and [referral recipient](CapabilityStatement-SDOHCC-ReferralRecipient.html) systems and - depending on the capabilities of the receivers - may also need to make the Tasks themselves available for query and support writing of procedures in situations where the recipient is a ['light' referral recipient](CapabilityStatement-SDOHCC-ReferralRecipient.html) that doesn't have local persistence or FHIR server capabilit
