# Verification packet SPOT-B03

11 findings — one verdict per key.

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
