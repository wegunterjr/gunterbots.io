# Robot Logic Lab — a Gunterbots school

Public waitlist site: [wegunterjr.github.io/gunterbots.io](https://wegunterjr.github.io/gunterbots.io/).

**Robot Logic Lab** is the club families join. **Gunterbots LLC** is the company. **GN2R** (Gunter) is the robot guide; members are a merry band of pirates. Engineering work (CTIS, custom robots) belongs on `gunterbots.com` later. This site is the school.

Crew lore and the wheels quest live at [Let's Make Wheels](https://wegunterjr.github.io/gunterbots_sentinel.io/lets-make-wheels.html).

Course content stays in the private repo `gunterbots-robot-logic-lab` and on Moodle at [learn.mgit.io](https://learn.mgit.io).

## Waitlist form

The form posts to n8n (`https://n8n.gunterbots.com/webhook/rll-waitlist`), which creates the Moodle user on learn.mgit.io. If n8n is down it falls back to [Formsubmit](https://formsubmit.co) at `hello@gunterbots.com`.

Setup: [docs/automation.md](docs/automation.md). Import [n8n/rll-waitlist.json](n8n/rll-waitlist.json).

## Custom domain

Point **gunterbots.com** at this GitHub Pages site (Cloudflare already holds the domain):

| Type | Name | Target | Proxy |
|---|---|---|---|
| CNAME | `@` | `wegunterjr.github.io` | DNS only until GitHub issues the cert |
| CNAME | `www` | `gunterbots.com` | DNS only |

Then GitHub → Settings → Pages → Custom domain `gunterbots.com`. This repo has a `CNAME` file.

Moodle stays at [learn.mgit.io](https://learn.mgit.io) until you change its wwwroot. Engineering / CTIS can take the apex later; move the school to `lab.gunterbots.com` when that happens.

## Go-live math

Scenario review before charging families (10 Explorers, one Inventor, lean vs $600 overhead):

- Shareable page: [docs/rollout.html](https://wegunterjr.github.io/gunterbots.io/docs/rollout.html)
- Markdown: [docs/rollout.md](docs/rollout.md)

Regenerate: `python3 docs/build_rollout_report.py`

## Local preview

```bash
python3 -m http.server 8080 --directory .
```

Open http://localhost:8080
