---
name: new-retailer-crawler
description: Scaffold a new retailer discount crawler (collector service) for the metax project end-to-end. Use when the user wants to add/onboard a new retailer, shop, or store to the discount collector — e.g. "add a crawler for foo.am", "onboard SAS", "new retailer scraper". Given a retailer's URL and a visual name (e.g. "SAS"), it discovers the discount page structure, extracts products, handles image-presentation pitfalls, wires every registration touchpoint, and verifies against the live site.
---

# New retailer crawler

Onboard a new retailer into the discount-collection pipeline. A collector crawls the retailer's
discount page and yields `DiscountedProduct` items; the pipeline embeds, categorizes, and serves them
through the Telegram bot.

The reference implementations to copy from live in
`metax/frameworks_and_drivers/ddd_patterns/services/discounted_product_collector_services/`:
- `sas_am.py` — paginated server-rendered HTML, tricky lazy/`<v-picture>` images.
- `tntesakan_am.py` — single server-rendered page, no pagination, swapped price spans, webp images.
- `yerevan_city.py` — JSON API (POST), no HTML parsing.

Read the one closest to the new site before writing anything.

## Step 0 — Gather inputs

Ask the user (in one message, accept whatever they already gave) for:

1. **Discount page URL** — the page/endpoint that lists discounted products (not the home page).
2. **Visual name** — the pretty label shown to users, e.g. `SAS`, `Yerevan City`.
3. **Slug** — the machine name, kebab-case, usually `<domain>-<tld>` e.g. `sas-am`, `foo-am`. Derive a
   default from the domain and confirm.
4. **Home page URL** and **phone number** — for the retailer admin row (can be filled later).
5. **Single-category?** — if the whole catalog is one category (like tntesakan.am), which one. This
   sets the retailer's `default_category` and skips the embedding classifier for its products.

Naming derived from the slug `foo-am`:
- enum member `FOO_AM = "foo-am"`
- module `foo_am.py`, class `FooAmCollectorService`
- creator `FooAmDiscountProductCollectorCreator`

## Step 1 — Reconnaissance: find the discounted products

Do not guess selectors. Fetch the real page and inspect it. Prefer a scratch script in the scratchpad
dir over ad-hoc shell so you can iterate.

```python
import httpx
r = httpx.get("<discount-url>", headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
              timeout=30, follow_redirects=True)
print(r.status_code, r.headers.get("content-type"))
print(r.text[:3000])
```

Decide the shape:
- **JSON API** (content-type json, or the page hydrates from an XHR) → copy `yerevan_city.py`. Open
  devtools/network mentally: many Armenian shops have an `api...`/`GetDiscounted` endpoint that returns
  everything in one POST. Prefer the API over HTML — it's stabler. Capture the request payload.
- **Server-rendered HTML** → copy `sas_am.py`/`tntesakan_am.py`, parse with BeautifulSoup + `lxml`.
- **Client-rendered (empty HTML shell, React/Vue)** → the products come from an XHR; find and use that
  JSON endpoint. Only reach for a headless browser as a last resort — none of the current collectors
  need one, and it complicates the runtime.

For HTML, locate: the product card container, and within a card the **name**, **original price**,
**discounted price**, **product link**, **image**. Confirm each selector against the fetched HTML
before coding. Watch for:
- Pagination — is there `?LIMIT=`/`?offset=`/`?page=`? (sas paginates; tntesakan is one page.) Find the
  total-count or last-page signal so you don't over- or under-fetch.
- Price spans that are **not** reliably ordered original-vs-sale (tntesakan) — derive real = max,
  discounted = min, and skip cards where the lower price is 0 (missing-original placeholder).
- Out-of-stock / unavailable badges — skip those cards; users can't buy them.

## Step 2 — Write the collector service

Create `.../discounted_product_collector_services/<slug>.py`. Subclass
`DiscountedProductCollectorService, DiscountedProductFieldsCleanerMixin` and implement the async
generator `collect(...)`. See `references/collector_template.py` for a fill-in-the-blanks HTML
template; for a JSON source, adapt `yerevan_city.py` instead.

Non-negotiable conventions (match the existing collectors exactly):
- `uuid.uuid7()` for each product's `uuid_`.
- Wrap name with `self.clean_discounted_product_name(...)` and each price with
  `Decimal(self.clean_discounted_product_price(...))`.
- `created_at`/`updated_at` = the passed `start_date_of_collecting`.
- `retailer_uuid=self._retailer.get_uuid()`, `category_uuid=None` (categorization happens downstream).
- `await asyncio.sleep(0.0)` after each yield (cooperative scheduling).
- On request failure: raise `InvalidUrlForScrappingError(invalid_url=...)` for `httpx.InvalidURL`;
  for other errors log via `logger.exception(...)` and `return`/`continue` — never crash the run.
- Send a browser `User-Agent`; use a generous `httpx.Timeout` and `follow_redirects=True` if needed.

## Step 3 — Handle image-presentation pitfalls

Images are the most common breakage. Work through this checklist for the new site — the current
collectors hit every one of these:

1. **Lazy loading** — the real URL is often in `data-src`/`data-original`, while `src` is a 1px or a
   `data:` placeholder. Prefer `data-src`, and reject any URL starting with `data:`.
2. **`<picture>` / framework tags** — sas.am uses `<v-picture>` with a JSON `:sources` attribute; parse
   it and pick the best candidate (`big_2x` → `big` → `middle` → …).
3. **Relative URLs** — resolve with `urljoin(<base>, src)` (or prefix the origin).
4. **webp / exotic formats & flaky origins** — Telegram may fail to fetch these. If the image host is
   unreliable for Telegram (IPv6-only, slow, webp), it must be routed through the weserv CDN — see
   Step 5's `_TELEGRAM_UNFETCHABLE_IMAGE_HOSTS`.
5. **Missing image** — set `image_url=None`; the bot substitutes a placeholder. Never yield a `data:`
   URI or empty string.

Verify by actually fetching a handful of the extracted image URLs (Step 6) — a `200` with an
`image/*` content-type. A URL that 404s or returns HTML is a bad selector.

## Step 4 — Register the slug (enables the admin row)

`metax/core/domain/entities/retailer/value_objects.py` — add the member to `RetailersNames`:

```python
FOO_AM = "foo-am"
```

The `RetailerModel.name` field's choices derive from this enum, so the admin cannot create the
retailer row until this exists.

## Step 5 — Wire the collector into the pipeline

1. **Creator** — in
   `metax/frameworks_and_drivers/design_patterns/factories/discounted_product_collector_service_creators.py`
   add a `FooAmDiscountProductCollectorCreator` (copy the `SasAm...` class verbatim, swap the type).
2. **Registration map** — in `metax/frameworks_and_drivers/taskiq_framework/tasks.py`: import the new
   creator and add `RetailersNames.FOO_AM: FooAmDiscountProductCollectorCreator,` to
   `RETAILER_NAME_DISCOUNTED_PRODUCT_COLLECTOR_SERVICE_CREATOR_MAP`.
3. **Visual name** — in `metax/frameworks_and_drivers/telegram_bot/localization.py` add to
   `_RETAILER_DISPLAY_NAMES`: `"foo-am": "Foo",` (this is the "SAS"-style label the user gave). Without
   it the bot title-cases the slug (`Foo Am`).
4. **Image host routing (only if Step 3 flagged it)** — in
   `metax/frameworks_and_drivers/telegram_bot/handlers/commands.py` add the image host to
   `_TELEGRAM_UNFETCHABLE_IMAGE_HOSTS` so product photos are mirrored through the weserv CDN.

## Step 6 — Verify against the live site

Write a scratch script (scratchpad dir) that constructs the collector with a throwaway `Retailer` and
runs `collect(...)`, then assert the crawl is healthy. Do not skip this — it's the whole point.

Check:
- **Count** — a plausible number of products (not 0, not absurdly low → selector broke; watch
  pagination terminates).
- **Prices** — `discounted_price < real_price`, both `> 0`, no absurd values (price-cleaning glitches).
- **URLs** — product `url` is absolute and looks like a product page.
- **Images** — for ~5 products, HTTP-fetch `image_url` and confirm `200` + `image/*`. If the host was
  added to `_TELEGRAM_UNFETCHABLE_IMAGE_HOSTS`, also fetch the weserv-wrapped URL.
- **No crash** — a transient network error must be swallowed (logged) not raised.

Then run the project's checks (ruff/mypy/pytest as configured) and `/verify` if the change has a
runtime surface to drive.

## Step 7 — Create the retailer row

Retailers are business data, created in the Django admin (not a migration). Tell the user to add a
`RetailerModel` in admin with: `name` = the slug (now selectable), `home_page_url`, `phone_number`,
and `default_category` only if Step 0 marked it single-category. The daily collection task picks it up
automatically via the registration map.

## Done — report

Summarize: the files touched (table), product count and a couple of sample products from the live
verify run, any image-host special-casing you added, and the one manual step left (create the admin
row). Flag anything fragile (aggressive selectors, unstable ordering) so the user knows what may need
maintenance.
