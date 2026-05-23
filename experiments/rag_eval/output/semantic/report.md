# RAG Evaluation Report

## Faithfulness
- Mean ± std: 0.306 ± 0.232

## Relevance
- Mean ± std: 0.264 ± 0.111

## Precision
- Mean ± std: 0.417 ± 0.360

## Context Relevance
- Mean ± std: 0.317 ± 0.079

## Recall
- Mean ± std: 0.133 ± 0.208

## Failure mode clusters
### noise-dominant
- Size: 5
- Mean scores:
  - faithfulness: 0.200
  - relevance: 0.195
  - precision: 0.040
  - context_relevance: 0.281
  - recall: 0.200
- Centroid example: Q: My data is really slow even though I have signal. | A: Sure, I can help with that! Just one quick question — Could you please let me know what type of device you're using? Once I have that, I'll walk you through the right fix.
- Worst examples:
  - Q: Cellular radio won't lock on to any band. | A: I want to make sure you get the right help here — I'm connecting you with one of our specialists who can sort this out. Insufficient information to resolve issue with confidence. Handing off to human support. Your case reference is CASE-USER_002-351. Someone will be in touch within 1 business day. You can also reach us directly through the SynthTel support portal if you need a faster response.
  - Q: My data is really slow even though I have signal. | A: Sure, I can help with that! Just one quick question — Could you please let me know what type of device you're using? Once I have that, I'll walk you through the right fix.
  - Q: My smartwatch lost its independent data connection. | A: Sure, I can help with that! Just one quick question — Could you please let me know the model of your smartwatch? Once I have that, I'll walk you through the right fix.
  - Q: How do I activate a new SIM card? | A: Sure, I can help with that! Just one quick question — Could you please let me know what type of device you're using with the new SIM card? Once I have that, I'll walk you through the right fix.
  - Q: My phone keeps cutting out inside the house. | A: Sure, I can help with that! Just one quick question — Could you please tell me what type of location you're in, like your home or office, and what kind of phone you're using? Once I have that, I'll walk you through the right fix.

### retrieval-gap-dominant
- Size: 4
- Mean scores:
  - faithfulness: 0.242
  - relevance: 0.379
  - precision: 0.800
  - context_relevance: 0.355
  - recall: 0.167
- Centroid example: Q: I want unlimited data for my whole family. | A: Based on your usage, I'd recommend the family_unlimited — I recommend the Family Unlimited plan for $130/month, as it provides unlimited data for your whole family, which is perfect for heavy users. It also includes 20 GB of hotspot data, so you can stay connected even when you're away from Wi-Fi.

If that doesn't quite fit, unlimited_plus, family_60gb could also work for you.

One thing to keep in mind: Deprioritized after 50 GB per line during congestion; Roaming add-on required.
- Worst examples:
  - Q: I landed in Paris and none of my apps are loading. | A: Based on your usage, I'd recommend the roaming_europe_pack with evidence ID ROAMING_EUROPE_PACK — The Europe Pack is the best choice for your stay in Paris, as it offers 8 GB of data and unlimited calls and SMS for just $35. It's perfect for your European trip and will keep you connected without breaking the bank. Just remember to activate it before you leave to ensure everything works smoothly!

If that doesn't quite fit, roaming_monthly_10gb, roaming_monthly_3gb could also work for you.

One thing to keep in mind: Only valid for 30 days from activation; Not available for countries outside Europe.
  - Q: I'm heading to Tokyo next week, will my phone work? | A: Based on your usage, I'd recommend the Japan/Korea Pack [ROAMING_JAPAN_KOREA] — The Japan/Korea Pack is the most cost-effective option for your trip to Tokyo at just $25 for 5 GB of data, plus unlimited calls and SMS while you're there. Just remember to activate it at least 24 hours before you leave to ensure everything is set up for your travels!

If that doesn't quite fit, International Roaming 3GB [ROAMING_MONTHLY_3GB], International Roaming 10GB [ROAMING_MONTHLY_10GB] could also work for you.

One thing to keep in mind: Only valid in Japan and South Korea; Must be activated at least 24 hours before departure.
  - Q: What's the cheapest plan that includes hotspot? | A: Based on your usage, I'd recommend the standard_20gb — The Standard 20GB plan at $45 per month is the most affordable option that includes hotspot usage, allowing you to use up to 5GB of data as a hotspot. This plan strikes a good balance between cost and data allowance, making it a solid choice for your needs.

If that doesn't quite fit, unlimited_plus, family_60gb could also work for you.

One thing to keep in mind: No roaming included; Hotspot is capped at 5 GB at full speed.
  - Q: I want unlimited data for my whole family. | A: Based on your usage, I'd recommend the family_unlimited — I recommend the Family Unlimited plan for $130/month, as it provides unlimited data for your whole family, which is perfect for heavy users. It also includes 20 GB of hotspot data, so you can stay connected even when you're away from Wi-Fi.

If that doesn't quite fit, unlimited_plus, family_60gb could also work for you.

One thing to keep in mind: Deprioritized after 50 GB per line during congestion; Roaming add-on required.

### retrieval-gap-dominant
- Size: 3
- Mean scores:
  - faithfulness: 0.567
  - relevance: 0.225
  - precision: 0.533
  - context_relevance: 0.325
  - recall: 0.000
- Centroid example: Q: My statement has an unexpected item I don't recognise. | A: Common reasons for a higher bill: 1. **Roaming charges:** Day Pass ($10/day) or unexpected international use 2. **Overage fees:** Exceeded data cap — $15 per additional GB on Basic and Standard plans 3. **Mid-cycle add-on:** Wearable add-on ($10/mo), tablet add-on ($20/mo) added during cycle and prorated You can check the full breakdown in MyAccount > Billing > Current Bill, and raise any disputes under Billing > Dispute a Charge.
- Worst examples:
  - Q: I want a refund for an unauthorized charge on my account. | A: I want to make sure you get the right help here — I'm connecting you with one of our specialists who can sort this out. Billing action requires a human agent (refund, dispute, or unauthorized charge). Your case reference is CASE-USER_001-345. Someone will be in touch within 1 business day. You can also reach us directly through the SynthTel support portal if you need a faster response.
  - Q: My statement has an unexpected item I don't recognise. | A: Common reasons for a higher bill: 1. **Roaming charges:** Day Pass ($10/day) or unexpected international use 2. **Overage fees:** Exceeded data cap — $15 per additional GB on Basic and Standard plans 3. **Mid-cycle add-on:** Wearable add-on ($10/mo), tablet add-on ($20/mo) added during cycle and prorated You can check the full breakdown in MyAccount > Billing > Current Bill, and raise any disputes under Billing > Dispute a Charge.
  - Q: Why is my bill higher than usual this month? | A: Common reasons for a higher bill: 1. **Roaming charges:** Day Pass ($10/day) or unexpected international use 2. **Overage fees:** Exceeded data cap — $15 per additional GB on Basic and Standard plans 3. **Mid-cycle add-on:** Wearable add-on ($10/mo), tablet add-on ($20/mo) added during cycle and prorated You can check the full breakdown in MyAccount > Billing > Current Bill, and raise any disputes under Billing > Dispute a Charge.
