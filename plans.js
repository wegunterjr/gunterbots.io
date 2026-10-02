/* Robot Logic Lab: one place for the checkout links.
 *
 * SEATS = "founding" while founding seats are open (first 20 families).
 * Change it to "regular" when they are gone: every Join button switches to $39 / $99,
 * and anything marked data-show="founding" hides while data-show="regular" appears.
 *
 * Buttons:   <a data-plan="explorer-monthly" href="#pricing">…</a>
 * Text:      <span data-show="founding">…</span> <span data-show="regular">…</span>
 * ?email=you@example.com on the page URL is passed to Stripe so the email is filled in.
 */
(function () {
  var SEATS = "founding";

  var LINKS = {
    founding: {
      "explorer-monthly": "https://buy.stripe.com/28E8wQb2Jeinbne1Pk7ss07",
      "inventor-monthly": "https://buy.stripe.com/cNi00kdaR5LR2QI79E7ss08",
      "explorer-season": "https://buy.stripe.com/5kQ9AU0o55LR62U0Lg7ss0b",
      "inventor-season": "https://buy.stripe.com/dRm4gA1s90rx9f679E7ss0c"
    },
    regular: {
      "explorer-monthly": "https://buy.stripe.com/3cIbJ21s90rx1ME0Lg7ss09",
      "inventor-monthly": "https://buy.stripe.com/eVqbJ2b2J2zF62UbpU7ss0a",
      "explorer-season": "https://buy.stripe.com/14A3cw3Ahcaf4YQ2To7ss0d",
      "inventor-season": "https://buy.stripe.com/28E28s7Qx6PV62U8dI7ss0e"
    }
  };

  window.RLL_SEATS = SEATS;
  function apply() {
    var email = new URLSearchParams(location.search).get("email") || "";
    document.querySelectorAll("[data-plan]").forEach(function (a) {
      var url = LINKS[SEATS][a.getAttribute("data-plan")];
      if (url) a.href = url + (email ? "?prefilled_email=" + encodeURIComponent(email) : "");
    });
    document.querySelectorAll("[data-show]").forEach(function (el) {
      el.hidden = el.getAttribute("data-show") !== SEATS;
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", apply);
  else apply();
})();
