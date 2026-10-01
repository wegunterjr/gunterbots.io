# Gunterbots Robot Logic Lab — landing page

Public waitlist site for [Robot Logic Lab](https://wegunterjr.github.io/gunterbots.io/).

GitHub Pages is the host (already signed in from this machine). Course content stays in the private repo `gunterbots-robot-logic-lab` and on Moodle at [learn.mgit.io](https://learn.mgit.io).

## Waitlist form

The form posts to [Formsubmit](https://formsubmit.co) at `hello@gunterbots.com`.

The first submission sends a confirmation email to that inbox. Click it or waitlist signups will sit unconfirmed.

`gunterbots.com` is already on Cloudflare. Point `hello@` with Cloudflare Email Routing to whatever inbox you actually read.

To change the destination, edit both the form `action` and the `fetch` URL in `index.html`.

## Custom domain later

`gunterbots.com` currently returns Cloudflare 522 (origin down). When you want the pretty URL:

1. In this repo, add a `CNAME` file containing `gunterbots.com`
2. GitHub → repo Settings → Pages → Custom domain
3. In Cloudflare DNS, CNAME `@` (or `www`) to `wegunterjr.github.io` and set the SSL mode to Full

## Local preview

```bash
python3 -m http.server 8080 --directory .
```

Open http://localhost:8080
