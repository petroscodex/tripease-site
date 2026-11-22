# Tripveller 1.1 capability matrix and site gaps

Checked 22 November 2026. App source is read-only: `https://github.com/petroscodex/TripEase` default branch `main`. Site source is `https://github.com/petroscodex/tripease-site`. Nothing here was deployed.

## What “1.1” is

The app people would install is still **version 1.0.0** (build `1.0.0+7`).

- `pubspec.yaml` `version: 1.0.0+7`
- `lib/config/app_info.dart` `kAppVersion = '1.0.0'`
- GitHub Releases list for TripEase is empty. No `v1.1` tag was published.
- `lib/features/labs.dart` says that with no tester switch and no Remote Config flag, every 1.1 switch is off and the app behaves as 1.0.

Live Firebase Remote Config values are not in the repo. The code default for `flag_v11_*` is false (`RemoteSettings.flag`, fallback false). Do not treat a 1.1 switch as on for the public.

## Store availability

Do not say the app is generally available.

- The site and this pass keep **App Store · coming soon** and **Google Play · coming soon**.
- Package id in the app is `com.petroscodex.tripease` (`android/app/build.gradle.kts`, `docs/RELEASE_CHECKLIST.md`).
- A public Google Play search on 22 November 2026 did not find that package. The Play results named “TripEase” are other publishers (`com.bytwiseapps.tripease`, `com.nichetravelplanner`). They are not Petros Codex.
- Family Sharing stays off the site and off Android materials. `docs/revenuecat.md` only tells a future App Store setup to turn Family Sharing on for the yearly iOS product. iOS is not launched. If it is added later, label it iOS only.

## Shipped on main (version string still 1.0.0)

These are in the default branch and are not behind a Labs switch. They are safe to describe as what the current app build does. They are not a public store release.

| Capability | Rule in code | Source |
|---|---|---|
| Free travellers and passports | 1 traveller, 1 passport | `lib/services/plan_limits.dart` (`freeTravellers`, `freePassportsPerTraveller`). Comment: Peter, 3 Nov 2026. Merged as PR #201 on 3 Nov 2026. |
| Free trips | 2 trips in any rolling 365 days | Same file, `freeTrips = 2`, `freeTripWindowDays = 365`. Comment: Peter, 22 Oct 2026. |
| Pro travellers and passports | Up to 10 travellers, up to 3 passports each | Same file. PR #201. |
| Pro trips | Unlimited | `PlanLimits.trips` returns null for Pro. |
| Best passport, form helper, booking import, wallet, widget, optional-form reminders, Schengen 90/180, all local services, landing weather | Pro, and `shipped: true` | `lib/services/feature_gate.dart`, `lib/models/paywall_feature.dart` |
| Local services on Free | 5 per country | `docs/revenuecat.md` and `Feature.services` free limit. Site already said 5. Not re-counted in this pass. |
| Land & Sea | Free for everyone. Sea-as-a-paid-mode and live tracking are `shipped: false` | `Feature.landMode` free; `Feature.seaMode` and `Feature.liveTracking` `shipped: false` |
| If Pro ends | Nothing is deleted. Extra travellers, passports and trips stay visible and locked. “Me” and the primary passport stay editable. The 2 most recent counted trips stay editable. | `lib/services/lapsed_access.dart`. PR #200, merged 3 Nov 2026. |
| Move to a new phone | Settings opens `/move-phone` with no feature flag. Export and import are a file the person sends. Wallet documents and passport scans are never in the file. Passport country is included only if that export turns it on. Tripveller does not upload the file. | `lib/screens/settings_screen.dart` key `settings-move-phone`, `lib/router/app_router.dart` `/move-phone`, `lib/services/data_transfer.dart` |
| Phrases | The translator stays closed until the person copies the phrase. | `lib/widgets/phrase_translate_sheet.dart`. PR #252, merged 19 Nov 2026. |
| Qibla | Settings opens `/qibla` with no feature flag. One-time approximate location, on the phone. | `lib/screens/settings_screen.dart`, `lib/router/app_router.dart`. **Not added to the public site in this pass.** `privacy.html` does not describe that prompt. |
| Referrals | Off unless the build is made with `--dart-define=REFERRALS=true`. Routes send people home when off. | `lib/config/referral_config.dart` |
| Prices | The paywall shows the store price. A trial line is shown only when the store offers a trial. There is no launch-price lock in the app. | `docs/revenuecat.md`. Site footnote already says there is no promise that a launch price lasts (site commit `f21d8337`, 18 Nov 2026). Left as-is. |
| Indicative US prices | US$4.99 a month and US$29.99 a year are the United States Google Play list prices in the site footnote, not an Apple price. | Same site commit. `docs/revenuecat.md` uses those figures as the intended store list. |

## Not shipped (do not put these in ads or on the site as available)

| Item | State on 22 Nov 2026 | Why it stays off |
|---|---|---|
| Labs 1.1 switches on main: partner offers, custom checklist, land trips, mode notes, stay clock, rules changed, link checker, where can we go, permits, calendar export, ready at desk | Code is on main. Each switch is off unless Remote Config `flag_v11_<slug>` is true, or a tester build turns it on. | `lib/features/labs.dart`. PR #230 merged 11 Nov 2026 and said the switches are off by default. |
| PR #241 Tripveller 1.1 (1/3) travel tools | Open draft | Not merged |
| PR #242 share card, Gift Pro, trip-tracker add-on, Cruise Pass scaffolds | Open draft. Still a draft on 22 Nov 2026. It was a draft on 17 Nov 2026. | Do not treat share cards as shipped. Buy buttons in that draft stay disabled. Cruise sample data is labelled sample. |
| PR #243 multi-leg trips and calendar import | Open draft, behind Labs switches, off by default | Site PR #73 (privacy, calendar) is also an open draft and says not to merge until Peter approves. It was not folded into this site PR. |
| PR #244, #245, #247, #248, #249 trip-rules data | Open, not merged | Not a public feature |
| PR #251 paywall guide prices | Open, not merged | Not a public feature |
| Cruises and trip tracking | Site already says they are coming as optional extras | Matches `shipped: false` and the unmerged scaffolds |
| Family Sharing | Not on the site | iOS only, and iOS is not launched |

## What the site said, and what this pass changed

Already correct on `main` before this pass (commit `f21d8337`): 10 travellers and 3 passports on Pro, lapsed Pro stays viewable and locked, trial only if the store offers it, no launch-price promise, stores coming soon, Family Sharing not in the plan list, cruises and tracking described as not ready.

This pass, on rolling PR #72:

- Free plan line is now **1 traveller, 1 saved passport, 2 trips in any 12 months**, in all 20 locales. The old line omitted the traveller.
- Home “What else” now says Settings includes Move to a new phone (export on the old phone, import on the new, Tripveller does not upload the file) and that a phrase is copied before a translator opens.
- Help no longer says the Move to a new phone screen is coming. It describes the screen that is already in the app.
- Help “What stays free if I cancel?” now matches the lapsed-Pro rule: extra travellers, passports and trips stay visible and locked, and nothing is deleted.
- Help release notes stay titled **Version 1.0**. They are not labelled 1.1. Four bullets were added for the limits, the lapsed-Pro lock, Move to a new phone, and copy-before-translate.
- The word “calm” was removed from the home lead, the two home photo descriptions, the Land & Sea lead, the help intro, and the press long description.
- Press kit now says the apps are coming soon and are not generally available, states the 10 / 3 Pro limits, and says border officials decide entry.

Not changed on purpose:

- No share card, Gift Pro, tracker, Cruise Pass, multi-leg, or calendar-import claim.
- No Family Sharing.
- No Qibla marketing line, because the privacy policy does not describe the location prompt yet.
- No new app screenshots. Old screenshot files were left in place.
- Pricing footnote from 18 Nov 2026 was left in place. `tools/legal-copy.test.mjs` requires the “no launch price” and “no Apple trial” sentences.
- Japanese home toggle said “年額・50%お得” for the English word “Yearly”. That was the old “save 50%” line. It now says “年額”. Other locales already translated “Yearly” without a 50% claim.

## Screenshots

The app could not be run here (private repo clone was rejected; GitHub read access was used instead). No new app UI was drawn or labelled as a capture.

Existing files under `assets/app/` are Tripveller screens already on the site, including the start screen “Where to next?” with the coral icon. They match the 1.0 start screen, not a 1.1 Labs screen. They were not renamed.

English set (12 screens, 390 and 780 widths): `start-where-to-next`, `visa-result-india`, `entry-thailand`, `land-home-busiest-crossings`, `just-landed-top`, `just-landed-full`, `just-landed-ride-apps`, `settings-privacy`, `crossing-el-amatillo`, `crossing-lo-wu`, `plugs-voltage-japan`, `tipping-australia`.

Locale folders exist for all 19 non-English locales. None of them has the full English set.

- No locale has `just-landed-full`, `just-landed-ride-apps`, `plugs-voltage-japan`, or `tipping-australia`. Those pages keep the English image.
- `crossing-el-amatillo` and `crossing-lo-wu` exist for Arabic and Brazilian Portuguese only.
- `settings-privacy` is missing for bn, fil, hi, id, it, ru, tr, ur, vi.

### Missing captures (do not fake these)

Needed before an ad or a new site frame can show the screen:

1. Settings → Move to a new phone (export and import).
2. Phrase sheet with Copy first, and the translator button only after that copy.
3. Travellers: Free shows one person; Pro shows the 10-traveller / 3-passport limit, including the paywall row.
4. Lapsed Pro: an extra traveller or trip visible and locked, not deleted.
5. Qibla, only after the privacy policy describes the one-time location prompt.
6. Any 1.1 Labs screen (share card, multi-leg route, calendar import, Gift Pro, Cruise Pass). Do not shoot these as the current product while the switches are off and PRs #241, #242 and #243 are unmerged drafts.

Locale gaps above are also missing captures. A localized ad should use a file that exists for that locale, or say the frame is English.

## Brand checks for this pass

- Name: Tripveller. Maker: Petros Codex.
- Tagline on the home page remains Arrive prepared.
- Teal `#0A756C` and coral `#E8604A` were not recolored. `#FFCC00` was not added.
- No Taiwan, Taipei, or Kinmen string was added. Simplified Chinese build check passed the blocked-term rule.
- The attached coral-background icon matches the mark already shipped on the site as icon cache `v14`. Video ads are out of scope here. Icon files were not replaced.
- Residual: French home cards still say “Volez serein”, “Roulez serein”, and “Naviguez serein”. Those are the existing translations of Fly Easy, Roam Easy, and Sail Easy. The English source does not say calm. A native pass can drop “serein” later. Italian “sereno” on the same cards is the same leftover.

## Competing site work

- PR #72 `fix/site-rolling` was open. It was one commit behind `main` and GitHub marked it dirty. `main` was merged in. The status fetch stays the root path `/data/status.json` with the 18 Nov unknown-date handling. The translation workflow still cancels a superseded run.
- PR #73 calendar privacy remains a separate draft. It was not merged into #72.
