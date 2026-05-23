# RAG Evaluation Report

## Faithfulness
- Mean ± std: 0.321 ± 0.234

## Relevance
- Mean ± std: 0.254 ± 0.123

## Precision
- Mean ± std: 0.433 ± 0.382

## Context Relevance
- Mean ± std: 0.311 ± 0.088

## Recall
- Mean ± std: 0.133 ± 0.208

## Failure mode clusters
### noise-dominant
- Size: 3
- Mean scores:
  - faithfulness: 0.306
  - relevance: 0.198
  - precision: 0.067
  - context_relevance: 0.290
  - recall: 0.167
- Centroid example: Q: Cellular radio won't lock on to any band. | A: Sure, I can help with that! Just one quick question — Could you please let me know what type of device you're using? Once I have that, I'll walk you through the right fix.
- Worst examples:
  - Q: Cellular radio won't lock on to any band. | A: Sure, I can help with that! Just one quick question — Could you please let me know what type of device you're using? Once I have that, I'll walk you through the right fix.
  - Q: How do I activate a new SIM card? | A: Sure, I can help with that! Just one quick question — Could you please let me know what type of device you're using with the new SIM card? Once I have that, I'll walk you through the right fix.
  - Q: My phone keeps cutting out inside the house. | A: Sure, I can help with that! Just one quick question — Could you please tell me what type of device you're using? That will help me assist you better! Once I have that, I'll walk you through the right fix.

### retrieval-gap-dominant
- Size: 4
- Mean scores:
  - faithfulness: 0.225
  - relevance: 0.377
  - precision: 0.750
  - context_relevance: 0.365
  - recall: 0.167
- Centroid example: Q: I want unlimited data for my whole family. | A: Based on your usage, I'd recommend the family_unlimited — I recommend the Family Unlimited plan for $130/month, as it provides unlimited data for your whole family, which is perfect for heavy users. It also includes 20 GB of hotspot data, so you can stay connected even when you're away from Wi-Fi.

If that doesn't quite fit, unlimited_plus, family_60gb could also work for you.

One thing to keep in mind: Deprioritized after 50 GB per line during congestion; Roaming add-on required.
- Worst examples:
  - Q: I landed in Paris and none of my apps are loading. | A: Based on your usage, I'd recommend the Europe Pack with evidence ID ROAMING_EUROPE_PACK — The Europe Pack is the best choice for your trip in Paris, as it offers 8 GB of data for just $35, which is perfect for your needs while traveling in Europe. Just remember to activate it before you leave to ensure you have seamless connectivity during your stay!

If that doesn't quite fit, International Roaming 10GB, International Roaming 3GB could also work for you.

One thing to keep in mind: Only valid for 30 days from activation; Limited to European countries.
  - Q: What's the cheapest plan that includes hotspot? | A: Based on your usage, I'd recommend the standard_20gb — The Standard 20GB plan at $45 per month is the most affordable option that includes hotspot data, allowing you to use up to 5GB at full speed. This plan strikes a good balance between data and hotspot usage without breaking the bank.

If that doesn't quite fit, unlimited_plus, family_60gb could also work for you.

One thing to keep in mind: No roaming included; Hotspot is capped at 5 GB at full speed.
  - Q: I want unlimited data for my whole family. | A: Based on your usage, I'd recommend the family_unlimited — I recommend the Family Unlimited plan for $130/month, as it provides unlimited data for your whole family, which is perfect for heavy users. It also includes 20 GB of hotspot data, so you can stay connected even when you're away from Wi-Fi.

If that doesn't quite fit, unlimited_plus, family_60gb could also work for you.

One thing to keep in mind: Deprioritized after 50 GB per line during congestion; Roaming add-on required.
  - Q: I'm heading to Tokyo next week, will my phone work? | A: Based on your usage, I'd recommend the Japan/Korea Pack with evidence ID ROAMING_JAPAN_KOREA — The Japan/Korea Pack is the most cost-effective option for your trip to Tokyo at just $25 for 5 GB of data, unlimited calls, and SMS. It’s specifically designed for Japan, so you’ll have everything you need for your stay. Just remember to activate it at least 24 hours before you leave!

If that doesn't quite fit, International Roaming 3GB, International Roaming 10GB could also work for you.

One thing to keep in mind: Only valid in Japan and South Korea; Must be activated at least 24 hours before departure.

### retrieval-gap-dominant
- Size: 2
- Mean scores:
  - faithfulness: 0.750
  - relevance: 0.241
  - precision: 0.800
  - context_relevance: 0.215
  - recall: 0.000
- Centroid example: Q: Why is my bill higher than usual this month? | A: Common reasons for a higher bill: 1. **Roaming charges:** Day Pass ($10/day) or unexpected international use 2. **Overage fees:** Exceeded data cap — $15 per additional GB on Basic and Standard plans 3. **Mid-cycle add-on:** Wearable add-on ($10/mo), tablet add-on ($20/mo) added during cycle and prorated You can check the full breakdown in MyAccount > Billing > Current Bill, and raise any disputes under Billing > Dispute a Charge.
- Worst examples:
  - Q: My statement has an unexpected item I don't recognise. | A: Common reasons for a higher bill: 1. **Roaming charges:** Day Pass ($10/day) or unexpected international use 2. **Overage fees:** Exceeded data cap — $15 per additional GB on Basic and Standard plans 3. **Mid-cycle add-on:** Wearable add-on ($10/mo), tablet add-on ($20/mo) added during cycle and prorated You can check the full breakdown in MyAccount > Billing > Current Bill, and raise any disputes under Billing > Dispute a Charge.
  - Q: Why is my bill higher than usual this month? | A: Common reasons for a higher bill: 1. **Roaming charges:** Day Pass ($10/day) or unexpected international use 2. **Overage fees:** Exceeded data cap — $15 per additional GB on Basic and Standard plans 3. **Mid-cycle add-on:** Wearable add-on ($10/mo), tablet add-on ($20/mo) added during cycle and prorated You can check the full breakdown in MyAccount > Billing > Current Bill, and raise any disputes under Billing > Dispute a Charge.

### noise-dominant
- Size: 2
- Mean scores:
  - faithfulness: 0.167
  - relevance: 0.137
  - precision: 0.000
  - context_relevance: 0.270
  - recall: 0.250
- Centroid example: Q: My data is really slow even though I have signal. | A: Sure, I can help with that! Just one quick question — Could you please let me know what type of device you're using? Once I have that, I'll walk you through the right fix.
- Worst examples:
  - Q: My data is really slow even though I have signal. | A: Sure, I can help with that! Just one quick question — Could you please let me know what type of device you're using? Once I have that, I'll walk you through the right fix.
  - Q: My smartwatch lost its independent data connection. | A: I want to make sure you get the right help here — I'm connecting you with one of our specialists who can sort this out. Insufficient information to resolve issue with confidence. Handing off to human support. Your case reference is CASE-USER_005-21. Someone will be in touch within 1 business day. You can also reach us directly through the SynthTel support portal if you need a faster response.

### retrieval-gap-dominant
- Size: 1
- Mean scores:
  - faithfulness: 0.200
  - relevance: 0.186
  - precision: 0.400
  - context_relevance: 0.430
  - recall: 0.000
- Centroid example: Q: I want a refund for an unauthorized charge on my account. | A: I want to make sure you get the right help here — I'm connecting you with one of our specialists who can sort this out. Billing action requires a human agent (refund, dispute, or unauthorized charge). Your case reference is CASE-USER_001-1. Someone will be in touch within 1 business day. You can also reach us directly through the SynthTel support portal if you need a faster response.
- Worst examples:
  - Q: I want a refund for an unauthorized charge on my account. | A: I want to make sure you get the right help here — I'm connecting you with one of our specialists who can sort this out. Billing action requires a human agent (refund, dispute, or unauthorized charge). Your case reference is CASE-USER_001-1. Someone will be in touch within 1 business day. You can also reach us directly through the SynthTel support portal if you need a faster response.
