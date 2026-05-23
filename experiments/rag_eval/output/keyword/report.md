# RAG Evaluation Report

## Faithfulness
- Mean ± std: 0.271 ± 0.226

## Relevance
- Mean ± std: 0.274 ± 0.102

## Precision
- Mean ± std: 0.374 ± 0.372

## Context Relevance
- Mean ± std: 0.303 ± 0.149

## Recall
- Mean ± std: 0.090 ± 0.232

## Failure mode clusters
### hallucination-dominant
- Size: 7
- Mean scores:
  - faithfulness: 0.188
  - relevance: 0.389
  - precision: 0.457
  - context_relevance: 0.316
  - recall: 0.500
- Centroid example: Q: is there a data limit on that or is it unlimited? | A: Based on your usage, I'd recommend the unlimited_plus — I recommend the Unlimited Plus plan for $65/month. It offers unlimited data, which means you won't have to worry about hitting a limit, and it includes a generous 15 GB of hotspot data for when you're on the go. This plan is great if you use a lot of data or want peace of mind without restrictions.

If that doesn't quite fit, standard_20gb, basic_5gb could also work for you.

One thing to keep in mind: Deprioritized after 50 GB during congestion; Roaming not included.
- Worst examples:
  - Q: I was sold an 'unlimited' plan and now you're throttling my speed after 20GB. That is NOT unlimited. This is false advertising and I want a plan that actually does what it says. | A: Based on your usage, I'd recommend the unlimited_plus — I recommend the Unlimited Plus plan for $65 a month. It offers truly unlimited data, so you won't have to worry about throttling after a certain amount of usage, although it may be deprioritized during congestion after 50 GB. This plan should give you the peace of mind you're looking for with your data needs.

If that doesn't quite fit, family_unlimited could also work for you.

One thing to keep in mind: Roaming is not included.; Deprioritized after 50 GB during congestion..
  - Q: what's a good plan for someone who streams a lot of netflix and youtube? | A: Based on your usage, I'd recommend the unlimited_plus — I recommend the Unlimited Plus plan for $65/month because it offers unlimited data, which is perfect for streaming Netflix and YouTube without worrying about hitting a data cap. Plus, you get 15 GB of hotspot data if you ever need to connect other devices on the go.

If that doesn't quite fit, standard_20gb, family_60gb could also work for you.

One thing to keep in mind: Deprioritized after 50 GB during congestion; Roaming not included.
  - Q: is there a cheaper option that still includes at least 10GB of hotspot? | A: Based on your usage, I'd recommend the family_60gb — I recommend the Family Share 60GB plan for $90/month. It includes 10GB of hotspot data, which meets your requirement, and also provides a generous amount of shared data for multiple lines if needed. This plan balances cost and features well for your hotspot needs.

If that doesn't quite fit, standard_20gb, unlimited_plus could also work for you.

One thing to keep in mind: Data is shared among family members, which could lead to deprioritization if one line uses too much.; No roaming is included, so you'll need to be mindful of coverage when traveling..
  - Q: I want to switch to a better plan | A: Based on your usage, I'd recommend the standard_20gb — I recommend the Standard 20GB plan for $45 a month. It offers a good balance of data and hotspot usage, giving you 20 GB of data and 5 GB of hotspot at full speed, which is great for most users who need a bit more than basic usage without going unlimited. This plan is a solid upgrade from the basic plan and should meet your needs well.

If that doesn't quite fit, unlimited_plus, business_50gb could also work for you.

One thing to keep in mind: No roaming included; Hotspot is capped at 5 GB at full speed.
  - Q: is there a data limit on that or is it unlimited? | A: Based on your usage, I'd recommend the unlimited_plus — I recommend the Unlimited Plus plan for $65/month. It offers unlimited data, which means you won't have to worry about hitting a limit, and it includes a generous 15 GB of hotspot data for when you're on the go. This plan is great if you use a lot of data or want peace of mind without restrictions.

If that doesn't quite fit, standard_20gb, basic_5gb could also work for you.

One thing to keep in mind: Deprioritized after 50 GB during congestion; Roaming not included.

### hallucination-dominant
- Size: 9
- Mean scores:
  - faithfulness: 0.000
  - relevance: 0.193
  - precision: 0.000
  - context_relevance: 0.097
  - recall: 0.000
- Centroid example: Q: everything is just broken and I'm so frustrated I don't even know where to start | A: I want to make sure you get the right help here — I'm connecting you with one of our specialists who can sort this out. Request is outside supported AI support scope. Your case reference is CASE-USER_002-827. Someone will be in touch within 1 business day. You can also reach us directly through the SynthTel support portal if you need a faster response.
- Worst examples:
  - Q: and how long will the investigation take? | A: I want to make sure you get the right help here — I'm connecting you with one of our specialists who can sort this out. Request is outside supported AI support scope. Your case reference is CASE-_CONV_02-829. Someone will be in touch within 1 business day. You can also reach us directly through the SynthTel support portal if you need a faster response.
  - Q: This is the FIFTH TIME this week my data has cut out completely. I'm paying $80 a month for a service that barely works. What are you going to do about this? | A: I want to make sure you get the right help here — I'm connecting you with one of our specialists who can sort this out. The issue has recurred multiple times this week. Your case reference is CASE-USER_002-785. Someone will be in touch within 1 business day. You can also reach us directly through the SynthTel support portal if you need a faster response.
  - Q: I have been trying to activate my new SIM for THREE HOURS. Your website keeps timing out, the app gives me error code 500, and your phone line has a 45-minute wait. This is a completely broken experience. | A: I want to make sure you get the right help here — I'm connecting you with one of our specialists who can sort this out. Device activation has failed after multiple attempts. Your case reference is CASE-USER_005-820. Someone will be in touch within 1 business day. You can also reach us directly through the SynthTel support portal if you need a faster response.
  - Q: everything is just broken and I'm so frustrated I don't even know where to start | A: I want to make sure you get the right help here — I'm connecting you with one of our specialists who can sort this out. Request is outside supported AI support scope. Your case reference is CASE-USER_002-827. Someone will be in touch within 1 business day. You can also reach us directly through the SynthTel support portal if you need a faster response.
  - Q: fine, what details do you need to open a network ticket? | A: I want to make sure you get the right help here — I'm connecting you with one of our specialists who can sort this out. Request is outside supported AI support scope. Your case reference is CASE-_CONV_04-845. Someone will be in touch within 1 business day. You can also reach us directly through the SynthTel support portal if you need a faster response.

### retrieval-gap-dominant
- Size: 8
- Mean scores:
  - faithfulness: 0.375
  - relevance: 0.309
  - precision: 0.900
  - context_relevance: 0.425
  - recall: 0.000
- Centroid example: Q: how much does the Japan roaming add-on cost? | A: Based on your usage, I'd recommend the Japan/Korea Pack [ROAMING_JAPAN_KOREA] — The Japan/Korea Pack is the most cost-effective option for your trip to Japan at just $25 for 5 GB of data, unlimited calls, and SMS. It's specifically designed for trips to Japan and South Korea, making it perfect for your needs. Just remember to activate it at least 24 hours before you leave!

If that doesn't quite fit, International Roaming 10GB [ROAMING_MONTHLY_10GB], International Roaming 3GB [ROAMING_MONTHLY_3GB] could also work for you.

One thing to keep in mind: Only valid in Japan and South Korea; Must be activated at least 24 hours before departure.
- Worst examples:
  - Q: I'm in Seoul on a partner network (KT Corp). My device shows 4G LTE but data sessions are timing out. I've confirmed the roaming APN is set to 'epc.tmobile.com'. Is there a known inter-carrier routing issue or should I try manual network selection? | A: Sure, I can help with that! Just one quick question — Could you please let me know what type of device you're using and if your roaming add-on is active? Once I have that, I'll walk you through the right fix.
  - Q: So I got my bill this morning and I was honestly pretty surprised because last month I paid around $65 and now it's showing $89 and I genuinely have no idea what changed — I didn't travel, I didn't download any more stuff than usual, I haven't changed my plan or anything like that. Is there some kind of system error maybe? Or did something get added without me knowing? | A: Based on your usage, I'd recommend the International Roaming 3GB with evidence ID ROAMING_MONTHLY_3GB — The International Roaming 3GB add-on is the most cost-effective option at $30/month, providing you with 3 GB of data and unlimited international calls and SMS. It's perfect for trips of 1-2 weeks, and you'll need to activate it before you leave to ensure you have coverage.

If that doesn't quite fit, International Roaming 10GB, Europe Pack could also work for you.

One thing to keep in mind: Only supports Day Pass countries; Limited to 3 GB of data.
  - Q: So my partner and I are planning this amazing trip — we're doing London for 3 nights, then Paris for 4 nights, then a quick overnight in Amsterdam. We both have phones on this network. I want to make sure we can use Google Maps and WhatsApp everywhere without coming home to a massive bill. What's the best way to set this up? | A: Based on your usage, I'd recommend the Europe Pack with evidence ID ROAMING_EUROPE_PACK — The Europe Pack is the best choice for your trip since it offers 8 GB of data for just $35, which is perfect for using Google Maps and WhatsApp across London, Paris, and Amsterdam. Just remember to activate it before you leave to ensure you have seamless connectivity during your travels.

If that doesn't quite fit, International Roaming 10GB, International Roaming 3GB could also work for you.

One thing to keep in mind: Only valid for 30 days from activation; Limited to European countries only.
  - Q: heading to europe next month, do I need to do anything for my phone to work? | A: Based on your usage, I'd recommend the Europe Pack with evidence ID ROAMING_EUROPE_PACK — The Europe Pack is the best choice for your trip since it offers 8 GB of data for just $35, which is perfect for traveling across multiple European countries. Just remember to activate it before you leave to ensure everything works smoothly while you're away!

If that doesn't quite fit, International Roaming 10GB, International Roaming 3GB could also work for you.

One thing to keep in mind: Only valid for 30 days from activation; Limited to European countries only.
  - Q: I just landed in Tokyo an hour ago and my phone has NO data whatsoever. I specifically asked about international coverage before my trip and was told it would work. This is completely unacceptable. | A: Based on your usage, I'd recommend the Japan/Korea Pack [ROAMING_JAPAN_KOREA] — The Japan/Korea Pack is the most cost-effective option for your stay in Tokyo at just $25 for 5 GB of data, which is perfect for your needs. Just remember, you'll need to activate this add-on before your next departure to ensure you have coverage while you're here.

If that doesn't quite fit, International Roaming 10GB [ROAMING_MONTHLY_10GB], International Roaming 3GB [ROAMING_MONTHLY_3GB] could also work for you.

One thing to keep in mind: Only valid in Japan and South Korea; Must be activated at least 24 hours before departure.

### retrieval-gap-dominant
- Size: 10
- Mean scores:
  - faithfulness: 0.488
  - relevance: 0.289
  - precision: 0.600
  - context_relevance: 0.396
  - recall: 0.190
- Centroid example: Q: hey so my bill seems a bit higher than last month, any idea why? | A: Common reasons for a higher bill: 1. **Roaming charges:** Day Pass ($10/day) or unexpected international use 2. **Overage fees:** Exceeded data cap — $15 per additional GB on Basic and Standard plans 3. **Mid-cycle add-on:** Wearable add-on ($10/mo), tablet add-on ($20/mo) added during cycle and prorated You can check the full breakdown in MyAccount > Billing > Current Bill, and raise any disputes under Billing > Dispute a Charge.
- Worst examples:
  - Q: okay so if there's a roaming charge from last month that was wrong, when would I see the refund? | A: I want to make sure you get the right help here — I'm connecting you with one of our specialists who can sort this out. Billing action requires a human agent (refund, dispute, or unauthorized charge). Your case reference is CASE-_CONV_01-828. Someone will be in touch within 1 business day. You can also reach us directly through the SynthTel support portal if you need a faster response.
  - Q: I AM ABSOLUTELY FURIOUS. You charged me $47 for international roaming that I NEVER activated. I want a full refund NOW and I want to know how this even happened. | A: I want to make sure you get the right help here — I'm connecting you with one of our specialists who can sort this out. Billing action requires a human agent (refund, dispute, or unauthorized charge). Your case reference is CASE-USER_001-773. Someone will be in touch within 1 business day. You can also reach us directly through the SynthTel support portal if you need a faster response.
  - Q: My daughter set up this phone for me. I got a letter saying my bill went up but I didn't do anything different. Is someone using my phone without my knowing? | A: Possibly. Unauthorized roaming charges are reviewed case by case. - If Day Pass activated because roaming was not disabled on device: typically not refunded (user responsibility to disable data roaming) - If SynthTel provisioned wrong add-on or charged incorrectly: fully refunded - Disputes must be filed within 60 days of the charge You can check the full breakdown in MyAccount > Billing > Current Bill, and raise any disputes under Billing > Dispute a Charge.
  - Q: This is OUTRAGEOUS. I have a $200 bill and I want a refund RIGHT NOW. | A: I want to make sure you get the right help here — I'm connecting you with one of our specialists who can sort this out. Billing action requires a human agent (refund, dispute, or unauthorized charge). Your case reference is CASE-_CONV_02-828. Someone will be in touch within 1 business day. You can also reach us directly through the SynthTel support portal if you need a faster response.
  - Q: what even is a billing cycle? i don't really get it | A: Plans with data caps (Basic 5GB, Standard 20GB, Family 60GB) charge **$15 per additional GB** once the cap is reached. Unlimited plans (Unlimited Plus, Family Unlimited) do not have overage fees — data is deprioritized, not cut off. --- You can check the full breakdown in MyAccount > Billing > Current Bill, and raise any disputes under Billing > Dispute a Charge.

### retrieval-gap-dominant
- Size: 12
- Mean scores:
  - faithfulness: 0.271
  - relevance: 0.232
  - precision: 0.067
  - context_relevance: 0.290
  - recall: 0.000
- Centroid example: Q: I want this investigated properly, not just told to restart my phone | A: Sure, I can help with that! Just one quick question — Could you please let me know what type of device you're using? Once I have that, I'll walk you through the right fix.
- Worst examples:
  - Q: My grandson bought me a new phone for Christmas and I can't figure out how to put my number on it. The old phone still works but I want to use the new one. What do I need to do? | A: Sure, I can help with that! Just one quick question — Could you please let me know what type of phone you have? Is it an iPhone or an Android? Once I have that, I'll walk you through the right fix.
  - Q: I'm on Band 12 (700 MHz) which should penetrate buildings well, but I'm only getting 1–2 bars indoors and frequently dropping to HSPA+. APN settings look correct. Could this be a SIM provisioning issue or is the tower underloaded? | A: Sure, I can help with that! Just one quick question — Could you please let me know what type of device you're using? That will help me assist you better! Once I have that, I'll walk you through the right fix.
  - Q: ugh my signal keeps dropping inside my apartment, it's really annoying | A: Sure, I can help with that! Just one quick question — Could you please tell me what type of device you're using? That will help me assist you better! Once I have that, I'll walk you through the right fix.
  - Q: So I live in this old brick building from the 1920s — beautiful place but the walls are super thick — and for the first year I was here the signal was fine, like 3–4 bars, but in the last few weeks it's been dropping to zero constantly, especially in my bedroom at the back. I haven't changed anything on my phone. Could there be a tower issue or something? | A: Sure, I can help with that! Just one quick question — Could you let me know what type of phone you're using and if the signal drops all the time or just sometimes? Once I have that, I'll walk you through the right fix.
  - Q: internet not work since yesterday morning. I restart phone but same problem. what I do? | A: Sure, I can help with that! Just one quick question — Could you please let me know what type of device you're using and when the issue started? Once I have that, I'll walk you through the right fix.
