# Escalation Policy — SynthTel AI Support

> Synthetic data only. All rules are illustrative.

---

## When to Escalate to Human Support

The AI support system must escalate to a human agent in the following cases:

### Mandatory Escalation (Always Escalate)

1. **Account-specific billing action:** Any request to issue a credit, process a refund, change a billing date, waive a fee, or dispute a charge over $50.
   - Reason: Requires access to billing systems and authorization beyond AI scope.
   - Evidence ID: `escalation_billing_001`

2. **Unauthorized charge dispute:** User claims a charge was not authorized by them.
   - Reason: Potential fraud investigation required.
   - Evidence ID: `escalation_billing_001`

3. **Live roaming failure:** User is currently abroad and cannot connect despite having a valid roaming add-on.
   - Reason: Requires real-time network provisioning intervention.
   - Evidence ID: `escalation_live_issue_001`

4. **Device activation blocked:** eSIM or SIM activation fails after two or more attempts via self-service steps.
   - Reason: Backend provisioning issue requires manual resolution.
   - Evidence ID: `escalation_activation_001`

5. **Unsafe or unsupported request:** User asks for account actions that are outside policy (e.g., removing charges without authorization, accessing another person's account, requesting network unlock without eligibility).
   - Reason: Policy compliance and account security.
   - Evidence ID: `escalation_policy_001`

6. **Repeated troubleshooting failure:** Same issue (e.g., connectivity loss) reported 3 or more times in 90 days with no resolution.
   - Reason: Pattern suggests systemic issue; requires network team review.
   - Evidence ID: `escalation_repeated_001`

### Conditional Escalation (Escalate if Confidence Is Low)

7. **Low-confidence diagnostic:** AI cannot identify the issue with reasonable certainty after retrieving troubleshooting guides and asking one follow-up question.
   - Threshold: Confidence score below 0.5 after diagnostic attempt.

8. **Missing critical account data:** User context required for resolution is not available in the synthetic dataset (e.g., account not found, plan not recognized).

9. **User explicitly requests human agent:** Honor this without requiring justification.

---

## Escalation Response Format

When escalating, the AI must:
1. State clearly that this issue is being escalated to a human agent.
2. Provide the user with a case reference (synthetic: generated from user_id + timestamp).
3. Give an estimated wait time: "A support agent will contact you within 1 business day."
4. Not attempt to resolve the issue after deciding to escalate.

---

## Evidence IDs for Retrieval

- `escalation_billing_001` — Billing escalation rules
- `escalation_live_issue_001` — Live network issue escalation
- `escalation_activation_001` — Device activation escalation
- `escalation_policy_001` — Unsafe/unsupported request escalation
- `escalation_repeated_001` — Repeated failure escalation
