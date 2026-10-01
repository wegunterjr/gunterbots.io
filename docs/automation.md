# Signup → Moodle, without doing it by hand

Use **n8n**. You already run it at [n8n.gunterbots.com](https://n8n.gunterbots.com). Moodle at learn.mgit.io already has the APIs (`core_user_create_users`, `enrol_manual_enrol_users`) on the Gunterbots Publisher service.

Zapier / Make / Moodle’s own enrolment keys also work. They add another bill and another login. n8n is the one that’s already on this domain.

## What gets automated

| Trigger | What n8n does |
|---|---|
| Waitlist form on the school site | Create the parent on learn.mgit.io (if they’re new), enrol them as a student in Robot Logic Lab (course 36), email them a password link, ping you |
| Someone emails hello@ instead of using the form | Auto-reply with the form link. Don’t parse free-form email into accounts — names and kids’ ages get messy |

Paid Inventor vs free Explorer vs Sentinel alumni is a **cohort** in Moodle, not a second user. n8n enrols everyone as a student. You (or a later n8n step) add the Founding / Inventor cohort when they pick a seat.

## One-time Moodle setup

1. Site administration → Server → Web services → External services → **Gunterbots Publisher**
2. Authorised users: the bot account
3. Create a token for that account + Gunterbots Publisher
4. Confirm these functions are on the service (they already are in `local_gunterbots`):
   - `core_user_get_users_by_field`
   - `core_user_create_users`
   - `enrol_manual_enrol_users`
   - `core_webservice_get_site_info`
5. Course **36** is Robot Logic Lab. Student role id is usually **5**. Check: the course → Participants → the Student role.

`createpassword=1` makes Moodle email the parent from learn.mgit.io: “set your password, then log in.” You never mail a password yourself.

## One-time n8n setup

1. Open [n8n.gunterbots.com](https://n8n.gunterbots.com)
2. Settings → Variables:
   - `MOODLE_URL` = `https://learn.mgit.io`
   - `MOODLE_TOKEN` = the token from above
   - `RLL_COURSE_ID` = `36`
   - `RLL_ROLE_ID` = `5`
   - `NOTIFY_EMAIL` = the inbox you actually read
3. Workflows → Import from file → `n8n/rll-waitlist.json` in this repo
4. Open the workflow → **Waitlist webhook** → copy the Production URL  
   It should be `https://n8n.gunterbots.com/webhook/rll-waitlist`
5. Turn the workflow **Active**
6. Test: submit the waitlist form once with your own email. You should land on thanks.html, Moodle should have a new user, and you should get a ping.

The site already posts to that webhook, then falls back to Formsubmit if n8n is down.

## Emails (the “they emailed me” path)

Don’t auto-create Moodle users from random email bodies.

1. Cloudflare → Email Routing: `hello@gunterbots.com` → your inbox
2. Optional n8n: IMAP / Gmail trigger on that mailbox → if the subject isn’t already a reply from Moodle, send a canned reply:

> Ahoy — grab a seat on the form so I can make your learn.mgit.io login without typing it by hand: https://gunterbots.com/#join

Former Sentinel families who reply “yes” to your crew email still use the form (put **Sentinel crew** in the note). n8n will see that string and tag the Moodle user.

## Domain: gunterbots.com

`gunterbots.com` is already on Cloudflare. The origin is down (522). `www` currently parks at Porkbun. Point both at this GitHub Pages site.

In Cloudflare DNS (this is the part I can’t click from here):

| Type | Name | Target | Proxy |
|---|---|---|---|
| CNAME | `@` | `wegunterjr.github.io` | DNS only (grey cloud) until the GitHub HTTPS cert issues |
| CNAME | `www` | `gunterbots.com` | DNS only, same |

Then GitHub → `wegunterjr/gunterbots.io` → Settings → Pages → Custom domain: `gunterbots.com`

This repo has a `CNAME` file for that.

Leave Moodle at **learn.mgit.io** for now. Moving it to `learn.gunterbots.com` means changing Moodle’s `$CFG->wwwroot` and the SSL vhost — do that as its own job.

Later, when the engineering/CTIS site is ready:

- `gunterbots.com` → a two-door hub (School / Engineering)
- School landing → `lab.gunterbots.com` (or `learning.gunterbots.com`)
- Moodle stays `learn.mgit.io` or becomes `learn.gunterbots.com`

That’s a DNS change, not a rebuild.

## What not to buy yet

- A second course platform just for billing. Keep Stripe/Kajabi for later; n8n + Moodle is enough to stop the manual account typing.
- Shipping kits, a custom app, or parsing every inbound email with an LLM.
