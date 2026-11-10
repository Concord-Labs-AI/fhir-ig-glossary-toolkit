# Verification packet SPOT-B03

3 findings — one verdict per key.

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
