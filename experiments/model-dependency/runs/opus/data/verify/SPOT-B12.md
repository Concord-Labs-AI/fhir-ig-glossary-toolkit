# Verification packet SPOT-B12

2 findings — one verdict per key.

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
