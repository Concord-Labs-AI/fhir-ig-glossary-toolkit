# Verification packet SPOT — spot check of unmatched findings

15 findings — one verdict per key.

## `input/pagecontent/connecting_applications_with_api_data_sources.md@1198`

- File: `input/pagecontent/connecting_applications_with_api_data_sources.md` line 13 (Prose, list-item)
- Type / terms / confidence: Missed use / T-CP / High
- Decision: —
- Issue: 'Referral platform' is used for the coordination platform (CP), which the glossary names with its aka 'community resource referral platform'.
- Find: `appropriate referral platforms`
- Replace: `appropriate coordination platforms`
- Context: 1. Applications are registered with the appropriate referral platforms.

## `input/pagecontent/connecting_applications_with_api_data_sources.md@1524`

- File: `input/pagecontent/connecting_applications_with_api_data_sources.md` line 15 (Prose, list-item)
- Type / terms / confidence: Missed use / T-CP / High
- Decision: —
- Issue: 'Referral platform' is used for the coordination platform (CP), which the glossary names with its aka 'community resource referral platform'.
- Find: `identify the referral platform`
- Replace: `identify the coordination platform`
- Context: * Patient/Client is provided a URL or a QR code. The patient uses this information to either find the app and install it on their mobile device, or to launch an on-line application. Optionally, the Patient/Client may be provided with a URL or code to identify the referral platform to the app. Alternatively, the patient might select the clinic/facility from a list within the app.

## `input/pagecontent/connecting_applications_with_api_data_sources.md@1713`

- File: `input/pagecontent/connecting_applications_with_api_data_sources.md` line 16 (Prose, list-item)
- Type / terms / confidence: Missed use / T-CP / High
- Decision: —
- Issue: 'Referral platform' is used for the coordination platform (CP), which the glossary names with its aka 'community resource referral platform'.
- Find: `connect to the referral platform`
- Replace: `connect to the coordination platform`
- Context: * Once the user has provided the information needed to connect to the referral platform, or has selected the platform, the app will attempt to access the FHIR API of the referral platform and will be redirected based on the platform's SMART App authentication process .

## `input/pagecontent/connecting_applications_with_api_data_sources.md@1812`

- File: `input/pagecontent/connecting_applications_with_api_data_sources.md` line 16 (Prose, list-item)
- Type / terms / confidence: Missed use / T-CP / High
- Decision: —
- Issue: 'Referral platform' is used for the coordination platform (CP), which the glossary names with its aka 'community resource referral platform'.
- Find: `FHIR API of the referral platform`
- Replace: `FHIR API of the coordination platform`
- Context: * Once the user has provided the information needed to connect to the referral platform, or has selected the platform, the app will attempt to access the FHIR API of the referral platform and will be redirected based on the platform's SMART App authentication process .

## `input/pagecontent/connecting_applications_with_api_data_sources.md@2695`

- File: `input/pagecontent/connecting_applications_with_api_data_sources.md` line 21 (Prose, list-item)
- Type / terms / confidence: Form / T-CP / High
- Decision: —
- Issue: 'Referral platform' is used for the coordination platform (CP), which the glossary names with its aka 'community resource referral platform'.
- Find: `to the Referral platform`
- Replace: `to the coordination platform`
- Context: * Application authenticates or allows the user to authenticate to the Referral platform and receives an access token

## `input/pagecontent/connecting_applications_with_api_data_sources.md@3413`

- File: `input/pagecontent/connecting_applications_with_api_data_sources.md` line 30 (Prose, list-item)
- Type / terms / confidence: Missed use / T-CP / High
- Decision: —
- Issue: 'Referral platform' is used for the coordination platform (CP), which the glossary names with its aka 'community resource referral platform'.
- Find: `appropriate referral platforms`
- Replace: `appropriate coordination platforms`
- Context: 1. Participating CBO applications are registered with the appropriate referral platforms (e.g., Epic, Unite US)

## `input/pagecontent/connecting_applications_with_api_data_sources.md@3612`

- File: `input/pagecontent/connecting_applications_with_api_data_sources.md` line 32 (Prose, list-item)
- Type / terms / confidence: Missed use / T-CP / High
- Decision: —
- Issue: 'Referral platform' is used for the coordination platform (CP), which the glossary names with its aka 'community resource referral platform'.
- Find: `provided by the referral platform`
- Replace: `provided by the coordination platform`
- Context: * CBO enters credentials provided by the referral platform

## `input/pagecontent/connecting_applications_with_api_data_sources.md@595`

- File: `input/pagecontent/connecting_applications_with_api_data_sources.md` line 7 (Prose, paragraph)
- Type / terms / confidence: Missed use / T-CP / High
- Decision: —
- Issue: 'Referral platform' is used for the coordination platform (CP), which the glossary names with its aka 'community resource referral platform'.
- Find: `all referral platforms and`
- Replace: `all coordination platforms and`
- Context: The intent of this section is to further standardize the interactions between FHIR APIs and consumer or CBO applications. §conn-1:To accomplish this, we recommend that the following processes **SHOULD** be supported by all referral platforms and applications to enable consistent processes to access data. The capability statements provide further specifications for servers.§

## `input/pagecontent/self_referral.md@2179`

- File: `input/pagecontent/self_referral.md` line 32 (Prose, list-item)
- Type / terms / confidence: Missed use / T-PAT / High
- Decision: D-2 (recommended: keep)
- Issue: Person reference in self-referral, where D-2 option B allows person; the glossary term is Patient.
- Find: `A person or an authorized`
- Replace: `A patient or an authorized`
- Context: - **Individual/Patient**: A person or an authorized representative of a person with one or more health-related social needs who initiates a search and request for services. The person is the subject of the referral.

## `input/pagecontent/self_referral.md@2205`

- File: `input/pagecontent/self_referral.md` line 32 (Prose, list-item)
- Type / terms / confidence: Missed use / T-PAT / High
- Decision: D-2 (recommended: keep)
- Issue: Person reference in self-referral, where D-2 option B allows person; the glossary term is Patient.
- Find: `representative of a person with`
- Replace: `representative of a patient with`
- Context: - **Individual/Patient**: A person or an authorized representative of a person with one or more health-related social needs who initiates a search and request for services. The person is the subject of the referral.

## `input/pagecontent/self_referral.md@7241`

- File: `input/pagecontent/self_referral.md` line 81 (Prose, paragraph)
- Type / terms / confidence: Missed use / T-PAT / High
- Decision: D-2 (recommended: keep)
- Issue: Person reference in self-referral, where D-2 option B allows individual; the glossary term is Patient.
- Find: `represents the individual or`
- Replace: `represents the patient or`
- Context: **NOTE**: `Task.requester` represents the system managing the referral workflow whereas ServiceRequest.requester represents the individual or entity asking for the service.



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

