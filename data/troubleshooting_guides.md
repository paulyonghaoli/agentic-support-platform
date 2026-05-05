# Troubleshooting Guides — SynthTel Network

> Synthetic data only. All steps and causes are illustrative.

---

## Guide: Mobile Data Not Working After Plan Change [TROUBLE_DATA_PLAN_CHANGE]

**Symptom:** User cannot use mobile data after switching to a new plan.

**Common causes:**
1. APN (Access Point Name) settings not updated after plan change
2. Provisioning delay (up to 2 hours after plan activation)
3. Device cache holding stale network settings
4. SIM card not re-registered on new plan

**Diagnostic slots required:**
- device_type (iPhone, Android, other)
- when_did_issue_start (immediately after change, or after delay)
- network_type (4G/LTE, 5G, no signal)

**Resolution steps:**
1. Toggle airplane mode off and on (forces network re-registration)
2. Restart device fully
3. Check APN settings:
   - iPhone: Settings > Cellular > Cellular Data Network — APN should be `synthtel.net`
   - Android: Settings > Network > Mobile Network > APN — set to `synthtel.net`
4. If no improvement after 15 minutes, remove and reinsert SIM (if physical SIM)
5. Reset network settings as last resort (note: removes saved Wi-Fi passwords)

**Escalate if:** Issue persists more than 2 hours after plan activation, or if APN settings are greyed out and cannot be changed.

---

## Guide: No Signal or Weak Signal Indoors [TROUBLE_INDOOR_SIGNAL]

**Symptom:** User loses signal indoors but has signal outdoors.

**Common causes:**
1. Building materials blocking signal (concrete, metal)
2. User is in a known coverage gap
3. Device antenna issue
4. Network congestion in area

**Diagnostic slots required:**
- location_type (home, office, specific building)
- device_type
- network_type (LTE vs 5G)
- frequency_of_issue (always, intermittent)

**Resolution steps:**
1. Enable Wi-Fi Calling (bypasses cellular for voice/SMS over Wi-Fi):
   - iPhone: Settings > Phone > Wi-Fi Calling
   - Android: varies by manufacturer; search "Wi-Fi Calling" in settings
2. Check if 5G is causing issue: switch to LTE-only mode and test
3. Move to window or higher floor to improve signal
4. Confirm coverage at address using SynthTel coverage checker

**Escalate if:** Wi-Fi Calling is unavailable on the plan, user reports repeated issues over multiple weeks, or network coverage map shows strong signal but user still has no signal (possible device fault or network node issue).

---

## Guide: Smartwatch Not Connecting to Cellular [TROUBLE_WATCH_CELLULAR]

**Symptom:** Smartwatch with standalone cellular is not connecting to mobile network.

**Common causes:**
1. Watch not added as a paired device on account
2. eSIM not provisioned or corrupted
3. Paired phone plan changed recently (requires eSIM reprovision)
4. Wearable add-on plan not active

**Diagnostic slots required:**
- watch_model (Apple Watch, Samsung Galaxy Watch, other)
- paired_phone_model
- account_has_wearable_addon (yes, no, unknown)
- recent_phone_plan_change (yes, no)

**Resolution steps:**
1. Confirm wearable add-on is active on account (costs $10/month)
2. Open paired phone app (Watch app for Apple Watch; Galaxy Wearable for Samsung):
   - Navigate to Cellular settings > Remove plan > Re-add plan
   - This re-provisions the eSIM
3. If eSIM reprovision fails, delete eSIM on watch (Settings > General > Remove eSIM) then re-activate from phone app
4. Restart both watch and phone after provisioning

**Escalate if:** eSIM provisioning fails more than twice, account shows add-on active but watch still cannot connect, or device model is not in the compatibility table.

---

## Guide: International Roaming Not Working [TROUBLE_ROAMING_NOT_WORKING]

**Symptom:** User is abroad and cannot connect to a local network.

**Common causes:**
1. Roaming add-on not activated before departure
2. Destination country not supported by current add-on
3. Data roaming not enabled in device settings
4. eSIM not configured for international use

**Diagnostic slots required:**
- current_country
- roaming_addon_active (yes, no, unknown)
- device_type
- esim_or_physical_sim

**Resolution steps:**
1. Verify data roaming is enabled: Settings > Cellular > Data Roaming (on)
2. Check if destination country is supported by active add-on
3. Confirm roaming add-on is active on account
4. Toggle airplane mode off/on after landing (forces carrier selection)
5. Manually select a carrier: Settings > Cellular > Network Selection > Manual, then choose available carrier

**Escalate if:** User has active roaming add-on, destination is supported, but still cannot connect (possible provisioning failure — requires back-end fix).

---

## Guide: Higher Than Expected Bill [TROUBLE_HIGH_BILL]

**Symptom:** User's bill is higher than their normal monthly cost.

**Common causes:**
1. Roaming charges from international travel
2. Overage charges (exceeded data cap)
3. Wearable or device add-on added mid-cycle
4. Premium SMS or third-party charges
5. Plan price increase

**Diagnostic slots required:**
- bill_increase_amount_approx
- traveled_internationally_this_month (yes, no)
- added_new_device_or_addon (yes, no)
- current_plan_id

**Resolution steps:**
1. Review itemized bill in account portal (MyAccount > Billing > Current Bill)
2. Check for roaming charges or overage fees
3. If unexpected third-party charge: can be disputed via account portal
4. If roaming charge not authorized by user: escalate to billing team

**Escalate if:** User disputes a charge as unauthorized, charge exceeds $50, or the charge relates to a billing error on SynthTel's side.

---

## Evidence IDs for Retrieval

- `trouble_data_plan_change_001` — Data not working after plan change
- `trouble_indoor_signal_001` — Indoor signal loss
- `trouble_watch_cellular_001` — Smartwatch cellular activation
- `trouble_roaming_not_working_001` — Roaming not working abroad
- `trouble_high_bill_001` — High bill troubleshooting
