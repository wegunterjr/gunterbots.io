# Robot Logic Lab — a Gunterbots school

Public waitlist site: [wegunterjr.github.io/gunterbots.io](https://wegunterjr.github.io/gunterbots.io/).

**Robot Logic Lab** is the club families join. **Gunterbots LLC** is the company. Engineering work (CTIS, custom robots) belongs on `gunterbots.com` later. This site is the school.

Course content stays in the private repo `gunterbots-robot-logic-lab` and on Moodle at [learn.mgit.io](https://learn.mgit.io).

## Waitlist form

The form posts to [Formsubmit](https://formsubmit.co) at `hello@gunterbots.com`.

The first submission sends a confirmation email to that inbox. Click it or waitlist signups will sit unconfirmed.

`gunterbots.com` is already on Cloudflare. Point `hello@` with Cloudflare Email Routing to whatever inbox you actually read.

To change the destination, edit both the form `action` and the `fetch` URL in `index.html`.

## Custom domain later

Keep `gunterbots.com` for the LLC / engineering work. Point the school at `learn.gunterbots.com`:

1. In this repo, add a `CNAME` file containing `learn.gunterbots.com`
2. GitHub → repo Settings → Pages → Custom domain
3. In Cloudflare DNS, CNAME `learn` to `wegunterjr.github.io` and set SSL to Full

## Local preview

```bash
python3 -m http.server 8080 --directory .
```

Open http://localhost:8080
