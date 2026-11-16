# HB-174 news data service

This service handles only `/newsroom/*`, `/api/news/v1/index.json`, and
`/news-sitemap.xml` on nice.okinawa. Existing articles and all other routes stay
on GitHub Pages. The Worker name is `nice-news-data-v1`.

Production remains gated by the repository rules: branch/PR, preview, Wan review,
merge, annotated `news-production-*` tag with `Wan-Verified: yes`. Authenticated
writer deployment requires explicit approval tied to the immutable release SHA
under current CLAUDE v1.19 (the old time window was removed). The tag must also
contain `Approved-SHA: <full commit>`. Do not invoke deploy.mjs locally.

One approved credential, `NICE_NEWS_CLOUDFLARE_API_TOKEN`, is scoped to Individual
Workers Editor on this Worker only. Its SHA256 is bound as
`NEWS_PUBLISH_TOKEN_SHA256`; the raw credential is never a public binding. The
same publication credential authenticates the Review-to-news delivery client.
It grants no zone, other Worker or direct storage privileges. Do not create a
second credential or reuse Plus credentials.

Before release, initialize a dedicated private R2 bucket `nice-news-data-v1`
and only the three public routes above via the existing management channel.
The bucket must have no public domain. CI deploys the Worker but does not edit
routes or create storage. Use the workers.dev address for protected writer
requests; anonymous writer/status requests must return 403.

The Review adapter must send only a locally recorded Wan-approved exact hash.
POST `/__news/publish` takes the document, id, hash, action, event_key, and
expected_generation. The event key is SHA256 of canonical `[id,hash,action]`.
GET `/__news/status` reports the generation or an event receipt, authenticated.
After an uncertain response, query that event; never call it a failed publication
or authorize a replacement version until its result is known. Publish receipts
and the public index must agree before Review marks the version published.

Immutable revisions are retained. A conditional R2 head write changes the four
languages, public index, sitemap and receipt together; concurrent writes return
409, never silently overwrite. Withdrawal removes only the selected exact hash
from the active head; archives remain. Public responses omit fact-check records,
reviewer identities, internal event receipts and draft content.

Rollback: remove only these newly introduced public route bindings to restore
the prior GitHub Pages behavior; roll the Worker back to initial `4102d122` if
needed. Preserve the bucket, journal and immutable revisions. No original news
file or URL should be deleted. HB-167 is not approved and must not be published.

Release is NOT ready until the delivery adapter, live empty-state checks,
configuration comparison, reverse-auth checks, and Wan preview have passed.
Local tests use an in-memory R2 fake; they are not proof of a live publication.
