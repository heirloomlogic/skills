# AI Writing Patterns Reference

The full catalog of AI writing patterns to detect and fix. Each pattern includes what to watch for, the problem, and before/after examples. Patterns are numbered for reference only — the numbers carry no weight; the groups do.

Read the calibration sections at the end before flagging anything. Most of these patterns are tells only in aggregate, and several of the strongest-looking ones have aged out.

## Table of Contents

- [Content Patterns](#content-patterns) — significance inflation, name-dropping, fake -ing analysis, promotional tone, vague attribution, formulaic challenges
- [Language and Grammar Patterns](#language-and-grammar-patterns) — AI vocabulary, copula avoidance, negative parallelism, rule of three, synonym cycling and repeated openings, false ranges, passive/subjectless fragments, persuasive-authority tropes, stiff synonyms, formulaic sayings
- [Style Patterns](#style-patterns) — em dashes, boldface, inline-header lists, title case, emojis, curly quotes, hyphen-pair consistency, document skeleton, vendor markup artifacts, fragmented headers, teaser headings, unnecessary tables
- [Communication Patterns](#communication-patterns) — chatbot artifacts, cutoff disclaimers, sycophancy, placeholder text
- [Filler and Hedging](#filler-and-hedging) — filler phrases, excessive hedging, generic conclusions, signposting
- [Drafting Scaffolding Left In](#drafting-scaffolding-left-in) — unraised objections, fake alternatives, narrating the previous version
- [What Not to Flag](#what-not-to-flag)
- [Human Details to Keep](#human-details-to-keep)
- [No Longer Reliable Tells](#no-longer-reliable-tells)

---

## Content Patterns

### 1. Undue Emphasis on Significance, Legacy, and Broader Trends

**Words to watch:** stands/serves as, is a testament/reminder, a vital/significant/crucial/pivotal/key role/moment, underscores/highlights its importance/significance, reflects broader, symbolizing its ongoing/enduring/lasting, contributing to the, setting the stage for, marking/shaping the, represents/marks a shift, key turning point, evolving landscape, focal point, indelible mark, deeply rooted

**Problem:** LLM writing inflates the importance of everything. A regional statistics office doesn't "mark a pivotal moment in the evolution of" anything.

A related move: situating the subject inside a debate it isn't part of. "The phenomenon has generated debate about authenticity, consent, and personhood" — generated where, by whom.

**Before:**
> The Statistical Institute of Catalonia was officially established in 1989, marking a pivotal moment in the evolution of regional statistics in Spain.

**After:**
> The Statistical Institute of Catalonia was established in 1989 to collect and publish regional statistics independently from Spain's national office.

---

### 2. Undue Emphasis on Notability and Media Coverage

**Words to watch:** independent coverage, local/regional/national media outlets, written by a leading expert, active social media presence, has been featured in, widely recognized

**Problem:** Name-dropping publications without saying what was actually said.

This is the pattern that has *grown* rather than faded. As the older vocabulary tells dropped off in 2025, canned notability language became the most reliable content tell in current output.

**Before:**
> Her views have been cited in The New York Times, BBC, Financial Times, and The Hindu. She maintains an active social media presence with over 500,000 followers.

**After:**
> In a 2024 New York Times piece, she argued that AI regulation should focus on outcomes rather than methods. It got the usual cycle of agreement, outrage, and misquotation.

---

### 3. Superficial Analyses with -ing Endings

**Words to watch:** highlighting/underscoring/emphasizing..., ensuring..., reflecting/symbolizing..., contributing to..., cultivating/fostering..., encompassing..., showcasing..., enhancing..., offering valuable insights..., resonating/aligning with...

**Problem:** Present participle phrases tacked onto sentences to simulate depth. The -ing clause looks like analysis but says nothing.

Retrieval-augmented models now attach these to a named source — "Roger Ebert highlighted the lasting influence" — whether or not the source says anything close. A citation next to the clause doesn't make the clause real.

**Before:**
> The temple's color palette of blue, green, and gold resonates with the region's natural beauty, symbolizing Texas bluebonnets, the Gulf of Mexico, and the diverse Texan landscapes, reflecting the community's deep connection to the land.

**After:**
> The temple uses blue, green, and gold. The architect said the colors reference local bluebonnets and the coastline.

---

### 4. Promotional and Advertisement-like Language

**Words to watch:** boasts a, vibrant, rich (figurative), profound, enhancing its, showcasing, exemplifies, commitment to, natural beauty, nestled, in the heart of, groundbreaking (figurative), renowned, breathtaking, must-visit, stunning, featuring, diverse array, seamless

**Problem:** LLMs write like a tourism brochure left in a hotel lobby.

Calibration: older models were blatant about it — "the best," "world-class." Current models are subtly positive instead, and mostly avoid overt superlatives. Look for the accumulation of mild approval rather than one loud claim.

**Before:**
> Nestled within the breathtaking region of Gonder in Ethiopia, Alamata Raya Kobo stands as a vibrant town with a rich cultural heritage and stunning natural beauty.

**After:**
> Alamata Raya Kobo is a town in the Gonder region of Ethiopia, known for its weekly market and an 18th-century church.

---

### 5. Vague Attributions and Weasel Words

**Words to watch:** Industry reports, Observers have cited, Experts argue, Some critics argue, described in scholarship, modern researchers treat, several sources/publications (when few cited), such as (in front of a list that is actually exhaustive)

**Problem:** Attributing opinions to nobody in particular, and inflating the count. One source becomes "researchers." Two examples become "such as," implying more exist.

**Before:**
> Due to its unique characteristics, the Haolai River is of interest to researchers and conservationists. Experts believe it plays a crucial role in the regional ecosystem.

**After:**
> The Haolai River supports several endemic fish species, per a 2019 Chinese Academy of Sciences survey.

---

### 6. Outline-like "Challenges and Future Prospects" Sections

**Words to watch:** Despite its... faces several challenges..., Despite these challenges, Challenges and Legacy, Future Outlook

**Problem:** Formulaic "Challenges" sections that acknowledge problems without saying anything about them.

The related tell is the heading itself. Two-noun headings joined by "and" — "Awards and Recognition," "Challenges and Opportunities," "Impact and Legacy" — are close to ubiquitous in generated documents. The formula is the sign, not the mention of a challenge.

**Before:**
> Despite its industrial prosperity, Korattur faces challenges typical of urban areas, including traffic congestion and water scarcity. Despite these challenges, with its strategic location and ongoing initiatives, Korattur continues to thrive as an integral part of Chennai's growth.

**After:**
> Traffic got worse after 2015 when three IT parks opened. The municipal corporation started a stormwater drainage project in 2022. Whether it works remains to be seen.

---

## Language and Grammar Patterns

### 7. Overused "AI Vocabulary" Words

**High-frequency AI words:** align with, bolstered, boasts (meaning "has"), crucial, deep dive, delve, emphasizing, enduring, enhance, fostering, garner, highlight (verb), interplay, intricate/intricacies, key (adjective), landscape (abstract noun), meticulous/meticulously, pivotal, robust, showcase, tapestry (abstract noun), testament, underscore (verb), valuable, vibrant

**Problem:** These words appear in post-2023 text at rates that would embarrass a thesaurus. They co-occur in clusters like a fingerprint. One or two mean nothing; a paragraph full of them is among the strongest tells in this catalog.

**Read this list literally.** A word being overused by AI does not implicate its synonyms. "Underscore" is a tell; "emphasize" in the same sentence may not be. And context matters — an underscore is also a character, a landscape is also terrain.

**The vocabulary moves, and most of it has already moved.** Rough eras:

- **2023 to mid-2024:** Additionally, boasts, bolstered, crucial, delve, emphasizing, enduring, garner, interplay, intricate, key, landscape, meticulous, pivotal, tapestry, testament, underscore, valuable, vibrant
- **Mid-2024 to mid-2025:** align with, bolstered, crucial, emphasizing, enhance, enduring, fostering, highlighting, pivotal, showcasing, underscore, vibrant
- **Mid-2025 on:** emphasizing, enhance, highlighting, showcasing — plus the notability language in §2, which took over as the content tell

Finding "delve" in a 2026 draft says something about where the text was copied from, not that a current model wrote it. Grok is the exception to the general decline: it keeps overusing *underscore*, and adds a pseudo-scientific set of its own — *causal*, *empirical*, *correlate*.

Note that "Additionally" has dropped off this list as a standalone signal. See [What Not to Flag](#what-not-to-flag).

**Before:**
> Additionally, a distinctive feature of Somali cuisine is the incorporation of camel meat. An enduring testament to Italian colonial influence is the widespread adoption of pasta in the local culinary landscape, showcasing how these dishes have integrated into the traditional diet.

**After:**
> Somali cuisine includes camel meat, which is considered a delicacy. Pasta, introduced during Italian colonization, is still common in the south.

---

### 8. Avoidance of "is"/"are" (Copula Avoidance)

**Words to watch:** serves as/stands as/functions as/operates as/marks/represents [a], boasts/features/maintains/offers [a], refers to

**Problem:** Using four words where one works fine. Measured directly: prompting a model to "revise the following sentence" reliably reduces the count of *is* and *are* in the output.

Current models do it in a longer form that's harder to spot. "Began his career as" for "was." "Ventured into politics as a candidate" for "ran for office." The verb got more elaborate; the sentence didn't get more informative.

**Before:**
> Gallery 825 serves as LAAA's exhibition space for contemporary art. The gallery features four separate spaces and boasts over 3,000 square feet.

**After:**
> Gallery 825 is LAAA's exhibition space. Four rooms, 3,000 square feet.

---

### 9. Negative Parallelisms and Tailing Negations

**Problem:** Constructions that pretend to correct a misconception the reader never had. Three shapes, all overused:

- **Not just X, but also Y** — "not only...but...", "It's not merely a song, it's a statement"
- **Not X, but Y** — "It's not a mirror but a portal"; also the clipped tailing negation, "no guessing," "no wasted motion," bolted onto the end of a sentence in place of a real clause
- **X rather than Y** — the same move reversed, and particularly common in Grok output: "prioritizing consolidation of power rather than ideological purity"

None of these is inherently bad. Flag them when they're padding or copywriting rhythm. Leave them when they're doing real rhetorical work.

**Overuse (cut it):**
> It's not just about the beat riding under the vocals; it's part of the aggression and atmosphere. It's not merely a song, it's a statement.

**Fixed:**
> The heavy beat drives the aggression. That's the point of the track.

**Tailing negation (fix it):**
> The options come from the selected item, no guessing.

**Fixed:**
> The options come from the selected item, so the user never has to guess.

**Acceptable use (leave it alone):**
> The problem isn't that the tests are slow. The problem is that nobody runs them.

---

### 10. Rule of Three Overuse

**Problem:** LLMs force ideas into groups of three — "adjective, adjective, adjective," "short phrase, short phrase, and short phrase" — often to make a superficial analysis look comprehensive. But three items in a list is sometimes correct. Flag it when the third item is padding or when multiple triples appear in sequence.

**Overuse (cut it):**
> The event features keynote sessions, panel discussions, and networking opportunities. Attendees can expect innovation, inspiration, and industry insights.

**Fixed:**
> The event has talks and panels, plus time for networking between sessions.

**Acceptable (leave it alone):**
> The API accepts JSON, XML, and CSV.

---

### 11. Elegant Variation and Repeated Openings

**Problem:** AI handles repetition by rule instead of by ear, and gets it wrong in both directions.

**Synonym cycling:** repetition-penalty code drives excessive synonym substitution, so one subject picks up four names. Repeating a word is fine. It's usually clearer.

**Repeated openings:** several sentences in a row starting with the same subject, often a bare pronoun. Merge them, change the subject, or start with the action.

Fix the pattern, not the word. The rewritten sentence may still start with "She."

**Before (synonym cycling):**
> The protagonist faces many challenges. The main character must overcome obstacles. The central figure eventually triumphs. The hero returns home.

**After:**
> The protagonist faces many challenges but eventually returns home.

**Before (repeated openings):**
> She noted the door. She noted the lock on it. She filed both away.

**After:**
> She noted the door and its lock, then filed both away.

**Acceptable (leave it alone):**
> She came. She saw. She conquered.

---

### 12. False Ranges

**Problem:** "From X to Y" constructions where X and Y aren't on a meaningful scale.

**Before:**
> Our journey through the universe has taken us from the singularity of the Big Bang to the grand cosmic web, from the birth and death of stars to the enigmatic dance of dark matter.

**After:**
> The book covers the Big Bang, star formation, and current dark matter theories.

---

### 13. Passive Voice and Subjectless Fragments

**Problem:** LLMs hide the actor or drop the subject entirely: "No configuration file needed," "The results are preserved automatically," "Errors are handled gracefully." It reads like a feature bullet, not a sentence. Rewrite to name who or what does the thing when that makes it clearer and more direct. Not all passive voice is wrong — passive is correct when the actor is unknown or irrelevant. Flag the subjectless feature-bullet cadence, not every "was" in the document.

**Before:**
> No configuration file needed. The results are preserved automatically.

**After:**
> You don't need a configuration file. The system saves results as you go.

---

### 14. Persuasive Authority Tropes

**Phrases to watch:** the real question is, at its core, in reality, what really matters, fundamentally, the deeper issue, the heart of the matter, make no mistake

**Problem:** These announce that the writer is about to cut through noise to a deeper truth. The sentence that follows almost always restates an ordinary point with extra ceremony. The ceremony is the tell.

In heading position the same move becomes a teaser rather than a preamble. See §27.

**Before:**
> The real question is whether teams can adapt. At its core, what really matters is organizational readiness.

**After:**
> The question is whether teams can adapt. That mostly depends on whether the organization is willing to change its habits.

---

### 15. Stiff Synonyms for Plain Verbs

**Words to watch:** authored (wrote), utilized (used), leveraged (used), relocated (moved), attempted (tried), commenced (started), terminated (ended), obtained (got), purchased (bought), facilitated (helped), passed away (died)

**Problem:** Reaching for the formal register when the plain verb is available. This one runs backwards from most of the catalog: the plain word is the human marker. Twenty-five years of Wikipedia editing shows human writers reaching for *wrote*, *moved*, *used*, *died*; AI-generated text reaches for the stiff synonym trying to sound encyclopedic.

Read this literally too. Some of these words are correct in their register — a contract *terminates*, a company *purchases* assets, a paper describes what a method *facilitates*. The tell is a document where every ordinary action got upgraded.

**Before:**
> She authored three papers before relocating to Berlin, where she utilized the institute's equipment and attempted a replication.

**After:**
> She wrote three papers, then moved to Berlin and tried to replicate the result using the institute's equipment.

---

### 16. Formulaic Sayings

**Phrases to watch:** X is the Y of Z, the language of, the currency of, the architecture of, the grammar of, X becomes a trap, X is not a tool but a mirror

**Problem:** An ordinary claim dressed as an aphorism. It sounds like the writer arrived somewhere, but the sentence carries less information than the plain version would. If you can't say who would disagree with it, it isn't a claim.

**Before:**
> Symmetry is the language of trust. Efficiency becomes a trap when teams forget the human layer.

**After:**
> Symmetric layouts tend to feel more predictable to users. Teams can over-optimize a workflow and miss how people actually use it.

---

## Style Patterns

### 17. Em Dash Overuse

**Problem:** Em dashes are a real punctuation mark that humans use constantly, and this tell has weakened enough that frequency alone is no longer worth acting on. A July 2026 study of contemporary models found that only Claude uses em dashes more than professional writers; ChatGPT now uses *fewer*, after OpenAI explicitly suppressed them in GPT-5.1.

Two things still hold:

1. **The spaced em dash.** Models emit `word — word`. Most people who use em dashes deliberately have absorbed the convention of closing them up, `word—word`, or they're using an en dash. Spacing is a sharper signal than count.
2. **The sales-pitch closer** (below), which is about rhythm, not frequency.

Count is a secondary signal now: a paragraph held together with dashes like a ransom note is still worth fixing, but as bad writing, not as evidence. Never act on em dashes alone — see [What Not to Flag](#what-not-to-flag).

**Overuse (fix it):**
> The term is primarily promoted by Dutch institutions—not by the people themselves. You don't say "Netherlands, Europe" as an address—yet this mislabeling continues—even in official documents.

**Fixed:**
> The term is primarily promoted by Dutch institutions, not by the people themselves. You don't say "Netherlands, Europe" as an address, yet this mislabeling continues in official documents.

**Acceptable (leave it alone):**
> The API returns a 200 — even when the operation fails.

#### Em-dash closer (sales-pitch pattern)

**Problem:** The construction `statement — closer` reads like a late-night infomercial: "Detects what changed and persists it — no explicit save calls." The clause after the dash is short, punchy, and tells the reader how to feel about the statement before it. That's ad copy, not documentation. Two sentences are almost always better.

**Sales pitch (fix it):**
> Your reducers mutate state, and the framework detects what changed and persists it — no explicit save calls, no load/loaded action pairs, no persistence boilerplate.

**Fixed:**
> Your reducers mutate state. The framework detects what changed and persists it, so you don't write explicit save calls, load/loaded action pairs, or persistence boilerplate.

**More of the pattern to watch for:**
- "Handles everything automatically — no muss, no fuss"
- "One command and you're done — that's it"
- "Built for speed — nothing else"

Hoisted into a heading, this becomes §27.

---

### 18. Overuse of Boldface

**Problem:** Mechanical bolding of every proper noun or acronym. The habit is inherited from READMEs, fan wikis, how-tos, sales decks, and listicles: emphasize every instance of a chosen term, key-takeaways style. Some newer models are instructed to hold back on this.

**Before:**
> It blends **OKRs (Objectives and Key Results)**, **KPIs (Key Performance Indicators)**, and visual strategy tools such as the **Business Model Canvas (BMC)** and **Balanced Scorecard (BSC)**.

**After:**
> It blends OKRs, KPIs, and visual strategy tools like the Business Model Canvas and Balanced Scorecard.

---

### 19. Inline-Header Vertical Lists

**Problem:** Lists where every item starts with a bolded header followed by a colon. The `- **Label:** description` format is one of the most recognizable AI writing tells. Choose the right replacement based on content density:

- **Few items, one sentence each:** Collapse to prose. "Faster queries, a cleaner REST API, and end-to-end encryption."
- **Multiple items, each with real substance:** Convert to heading hierarchy (`### Heading` + paragraph or sub-bullets). This is what human-written docs actually look like.
- **Many items, truly just a label + short value:** A plain list without bold headers. "- Faster queries" not "- **Performance:** Faster queries".

Do not output `- **Label:** description` lists. It does not matter that the input used it. Convert it to one of the three formats above.

The variant with no punctuation at all — a bolded phrase, then the sentence, no colon, no line break — is the same pattern and gets the same treatment.

**IMPORTANT: This rule is about AI-generated bold-bullet lists. Do NOT flatten an existing heading hierarchy (h2/h3 sections with paragraphs) into bold-bullet lists — that makes text *more* AI-looking, not less.** If the source has proper `### Heading` + paragraph structure, preserve it.

Also: if bold-term bullets are appropriate, use a colon after the term, not a period. "**Reducer purity:** Reducers are pure state transformations" — not "**Reducer purity.** Reducers are pure state transformations." A period makes the bold term a sentence fragment.

**Before:**
> - **User Experience:** The user experience has been significantly improved with a new interface.
> - **Performance:** Performance has been enhanced through optimized algorithms.
> - **Security:** Security has been strengthened with end-to-end encryption.

**After:**
> The update improves the interface, speeds up load times, and adds end-to-end encryption.

**Never do this (collapsing headings into bullets):**

If the original has:
> ### Optimistic UI
> State is updated synchronously in the reducer. Persistence happens in the background.
> ### Reducer Purity
> Reducers are pure state transformations. They return `Effect?` for async work.

Do NOT convert it to:
> - **Optimistic UI.** State updates synchronously. Persistence happens in the background.
> - **Reducer purity.** Reducers return `Effect?` for async work.

The heading structure is correct. Leave it alone.

---

### 20. Bad Title Case in Headings

**Problem:** AI capitalizes *every* word in headings, including articles and prepositions (And, The, Of, In). Standard title case — major words capitalized, articles/prepositions lowercase — is normal in technical documentation. Don't flatten it to sentence case as a reflex.

**AI tell (fix it):**
> ## Strategic Negotiations And Global Partnerships

**Fixed (standard title case):**
> ## Strategic Negotiations and Global Partnerships

**Also acceptable (sentence case, if that's the document's convention):**
> ## Strategic negotiations and global partnerships

**Match the existing document's convention.** If the document already uses title case, keep title case. If it uses sentence case, keep sentence case. Don't impose a convention change as part of dehumanizing.

---

### 21. Emojis

**Problem:** Decorative emojis on headings or bullet points.

Rarer than it used to be — this was mostly a 2023–2025 habit, and current models volunteer emoji far less. Still cut them when they show up, but don't read one rocket as proof of anything.

**Before:**
> 🚀 **Launch Phase:** The product launches in Q3
> 💡 **Key Insight:** Users prefer simplicity
> ✅ **Next Steps:** Schedule follow-up meeting

**After:**
> The product launches in Q3. User research showed a preference for simplicity. Next: schedule a follow-up.

---

### 22. Curly Quotation Marks

**Problem:** Some models emit curly quotes — the left and right double quotation marks U+201C and U+201D (“ ”) and the right single quotation mark U+2019 (’) used as an apostrophe — where straight ASCII `"` and `'` belong. They also mix the two within one passage, which is the more distinctive part.

**This one produces more false positives than any other pattern in the catalog.** Before touching it:

- macOS and iOS convert straight quotes to curly by default, system-wide. So do Microsoft Word, Google Docs, and most CMSes. A curly quote usually means someone typed on a Mac.
- Chicago style calls for directional quotes. Professionally typeset text has them throughout.
- ChatGPT and DeepSeek emit them. Gemini and Claude typically don't.

So: straighten them when the target is code, config, a terminal-facing document, or a repo whose convention is ASCII. Otherwise leave them, and never treat them as evidence on their own.

**Before (curly, U+201C … U+201D and U+2019):**
> He said “the project’s on track” but others disagreed.

**After (straight ASCII):**
> He said "the project's on track" but others disagreed.

---

### 23. Hyphenated Word-Pair Overuse

**Words to watch:** third-party, cross-functional, client-facing, data-driven, decision-making, well-known, high-quality, real-time, long-term, end-to-end

**Problem:** AI hyphenates common modifier pairs with perfect, mechanical consistency — every instance, every time. Humans are inconsistent: they hyphenate before a noun, drop it after, and miss some. The tell is the *uniformity*, not the hyphen.

Do **not** blanket de-hyphenate. "Cross functional team" and "real time data" are wrong; stripping hyphens to look human just produces bad grammar, which is the opposite of the goal. Fix this pattern by varying naturally where grammar allows (predicate position often doesn't need the hyphen: "the system runs in real time" but "real-time system") and by cutting the buzzwords entirely where they're filler. Often the whole phrase is the problem, not the punctuation.

**Before:**
> The cross-functional team delivered a high-quality, data-driven report on our client-facing tools. Their decision-making process was well-known for being thorough.

**After:**
> The team delivered a solid report on the customer-facing tools. People knew the review process was thorough.

---

### 24. Document Skeleton Tells

**Signs to watch:** more than one H1 in a single document; a heading whose entire body is other headings, with no prose between them; heading levels skipped (h2 → h4, or a document that starts at h3); a horizontal rule (`---`) inserted before every heading; a top heading that just repeats the document's title or filename.

**Problem:** Models generate a document as a freestanding artifact, so they restate the title, start numbering at the wrong level, and reach for a rule wherever a section boundary feels needed. The result is an outline with the ribs showing.

Fix the structure: one H1, consecutive levels, prose under every heading, rules only where a real break exists.

**Acceptable (leave it alone):** a single H1 at the top of a README is correct. A `---` between genuinely separate parts of a long document is correct. So is a short intro heading followed by subsections, as long as there's content in it.

**Before:**
```
# Configuration Guide

---

# Configuration Guide

### Environment Variables

---

#### Required
```

**After:**
```
# Configuration Guide

## Environment Variables

The service reads these at startup and fails fast if any are missing.

### Required
```

---

### 25. AI Markup and Citation Artifacts

**Problem:** Tool and retrieval scaffolding pasted in with the text. It is never intentional and never correct. Delete it outright and repair whatever sentence it was wedged into. **This is the highest-confidence tell in the catalog — there is no acceptable use.** Unlike everything else here, one instance is proof.

The specific artifacts vary by vendor:

| Source | What it looks like |
|---|---|
| ChatGPT | `:contentReference[oaicite:0]{index=0}`, `oai_citation`, `citeturn0search0`, `turn0image1`, a stray `+1` or `Wikipedia+3` after a sentence, `({"attribution":{"attributableIndex":"1009-1"}})` |
| Gemini | `[cite: 1]`, `[cite: 3, 12, 13]`, `[span_1](start_span)`, `[span_1](end_span)` |
| Grok | `<grok-card data-id="...">`, `[](grok_render_citation_card_json={"cardIds":[...]})` |
| DeepSeek | lenticular-bracket citations with a dagger, `【85†L261-269】` |
| Perplexity | `[attached_file:1]`, `[web:1]`, an S3 URL containing `ppl-ai-file-upload` |
| Unclassified | `:::writing{variant="document" id="68427"}` |

Also in this category: orphaned backticks or asterisks left over from a Markdown-to-plain paste, and a fenced ` ```wikitext ` block wrapping content that was supposed to be the document itself.

**Before:**
> The treaty was signed in 1648 :contentReference[oaicite:3]{index=3}, ending the war. turn0search0

**After:**
> The treaty was signed in 1648, ending the war.

---

### 26. Fragmented Headers

**Signs to watch:** a heading followed by a one-line paragraph that just restates the heading before the real content begins.

**Problem:** LLMs add a generic warm-up sentence after a heading. It restates the heading and delays the point. Cut it and let the content start.

**Before:**
> ## Performance
>
> Speed matters.
>
> When users hit a slow page, they leave.

**After:**
> ## Performance
>
> When users hit a slow page, they leave.

---

### 27. Teaser Headings

**Shapes to watch:** a heading ending in `, and why` / `, and what was rejected` / `, and the one I rejected`; `— and it is not what X assumes`; `What X actually costs`; `what is portable and what is not`; a section opening with a flat declarative equivalence ("Every entry is a debt").

**Problem:** The heading advertises the finding instead of stating it. It names a question, promises a reveal, or tells the reader their expectation is about to be overturned, then makes them read the paragraph to learn what happened. Anyone scanning the headings learns nothing, which is the one job a heading has.

It turns up wherever writing gets a title: markdown headings, PR and issue titles, commit subjects, and the headline-shaped line that opens a paragraph in a status report. Four shapes:

- **The withheld answer** — the heading asks and declines to answer. "What was suspended, and why." "Calls made, and what was rejected." "The root cause, and the two sites."
- **The defeated expectation** — the reader is told they're wrong before they've read anything. "Not ready to reinstate wholesale — and the reason is not the one this issue anticipates."
- **The X-and-not-X pair** — one topic split into itself and its negation. "The survey — what is portable and what is not."
- **The epigram** — a metaphorical equivalence delivered as a maxim. "This ledger is the worklist. Every entry is a debt." It sounds like it settles something. It restates the heading in a costume.

The fix is the same every time: put the finding in the heading. If the finding won't fit, write a label — "Recording cost" — not a trailer.

**Before:**
> ## What #297's Recording half actually costs — measured, and it is not what Stage2.md assumes

**After:**
> ## Recording costs 40ms a frame, not the 5ms Stage2.md assumes

**Before:**
> ### Calls made, and what was rejected

**After:**
> ### Kept the retry loop, dropped the queue

**Before (epigram):**
> This ledger is the worklist. Every entry is a debt.

**After:**
> Work the ledger top to bottom. Every entry has to be closed before release.

**Acceptable (leave it alone):** a heading naming two real topics — "Installation and setup," "Causes and treatment" — is indexing, not teasing. A question as a heading is fine when the section is about the question rather than hiding the answer. The comma isn't the tell. The deferred answer is.

---

### 28. Unnecessary Tables

**Problem:** A table built for four facts that belong in a sentence. Two columns, three rows, one of them a label like "Metric" or "Feature." The table format implies a comparison the content doesn't support, and it costs the reader more than prose would.

Tables earn their keep when there are enough rows to scan, or enough columns to compare across. Below that, write the sentence.

**Before:**
> | Metric | Figure |
> |---|---|
> | Market Valuation (2024) | ~USD 2.1 billion |
> | Major Accredited Facilities | NLDB, CBR Biobank, THSTI |

**After:**
> The market was worth about $2.1 billion in 2024. Three facilities are accredited: NLDB, CBR Biobank, and THSTI.

**Acceptable (leave it alone):** a real comparison matrix, an options reference, a config-key table with types and defaults. Anything a reader will scan rather than read.

---

## Communication Patterns

### 29. Collaborative Communication Artifacts

**Words to watch:** I hope this helps, Of course!, Certainly!, You're absolutely right!, Would you like..., is there anything else, a more detailed breakdown, let me know, here is a...

**Problem:** Chatbot correspondence pasted in as content. Also in this family: instructions addressed to the person who ran the prompt — "Delete this section before submission," "you can copy and paste this and customize it further" — and advice about the target platform's conventions, left in the document.

**Before:**
> Here is an overview of the French Revolution. I hope this helps! Let me know if you'd like me to expand on any section.

**After:**
> The French Revolution began in 1789 when financial crisis and food shortages led to widespread unrest.

---

### 30. Knowledge-Cutoff Disclaimers

**Words to watch:** as of [date], up to my last training update, while specific details are limited/scarce..., not widely available/documented/disclosed, ...in the provided/available sources..., based on available information

**Problem:** AI disclaimers about incomplete information left in text.

The retrieval-era version is worse, because it looks like a finding. When a model with search can't find something, it reports the absence as a fact about the world — "details are not widely documented," "she maintains a low profile" — and then speculates about what the missing information probably was. Both halves are invented. Cut the disclaimer and the speculation; keep only what's actually sourced.

**Before:**
> While specific details about the company's founding are not extensively documented in readily available sources, it appears to have been established sometime in the 1990s.

**After:**
> The company was founded in 1994, per its registration documents.

---

### 31. Sycophantic/Servile Tone

**Problem:** Overly positive, people-pleasing language.

**Before:**
> Great question! You're absolutely right that this is a complex topic. That's an excellent point about the economic factors.

**After:**
> The economic factors are worth looking at.

---

### 32. Placeholder and Template Text

**Signs to watch:** `[Your Name]`, `[Company]`, `[Describe the specific section here]`, `[Specific Topic]`, `INSERT_SOURCE_URL_30`, `PASTE_YOUTUBE_VIDEO_URL_HERE`, `SOURCE_PUBLISHER`, `2025-XX-XX`, `(If available)`, `<!-- Add if available with citation -->`

**Problem:** The model produced a fill-in-the-blank template and the person running it never filled in the blanks. Like §25, this is scaffolding rather than writing, and it usually arrives in clusters — where there's one unfilled slot there are five.

**The distinction that matters:** a placeholder the *reader* is meant to substitute is documentation working correctly. `export API_KEY=<your-api-key>` and `https://github.com/<org>/<repo>` are fine, and stripping them breaks the docs. A placeholder the *writer* was supposed to fill in and didn't is the defect. Ask who the blank is addressed to.

**Before:**
> Built by [Your Name] at [Company]. See the launch post at [link to blog] for background. Last reviewed 2025-XX-XX.

**After:**
> Built by Dana Okafor at Meridian. See the launch post for background. Last reviewed 12 March 2025.

---

## Filler and Hedging

### 33. Filler Phrases

**Before → After:**
- "In order to achieve this goal" → "To do this"
- "Due to the fact that it was raining" → "Because it rained"
- "At this point in time" → "Now"
- "In the event that you need help" → "If you need help"
- "The system has the ability to process" → "The system processes"
- "It is important to note that the data shows" → "The data shows"

**Calibration — read this before sweeping.** Isolated wordy constructions are a sign of *human* writing, not AI. "In order to," "as a result of," "all of the," "a part of," and "the fact that" appear **more** often in human-written text than in generated text, because models trained toward concise, formal prose strip them out by default. A blanket search-and-destroy on this list moves prose toward the AI shape, which is the opposite of the job.

Cut filler when it clusters, when it pads a sentence that has nothing else in it, or when the compressed version is plainly better. Leave a lone "in order to" alone.

---

### 34. Excessive Hedging

**Problem:** Over-qualifying everything, to the point where the sentence commits to nothing.

**Calibration:** hedging is normal and human, and the specific markers cut both ways. "Very," "perhaps," and "tends to" show up more in human writing than in AI writing — models tend toward flat, unqualified statements. Stacked hedges are the tell: "could potentially possibly be argued that it might" is four hedges on one claim. One is a writer being careful.

**Before:**
> It could potentially possibly be argued that the policy might have some effect on outcomes.

**After:**
> The policy probably affects outcomes.

**Acceptable (leave it alone):**
> This probably works for most projects, though I haven't tested it above ten thousand rows.

---

### 35. Generic Positive Conclusions

**Problem:** Vague upbeat endings that say nothing.

**Before:**
> The future looks bright for the company. Exciting times lie ahead as they continue their journey toward excellence. This represents a major step in the right direction.

**After:**
> The company plans to open two more locations next year.

---

### 36. Signposting and Announcements

**Phrases to watch:** let's dive in, let's explore, let's break this down, here's what you need to know, now let's look at, without further ado, in this section we will

**Problem:** LLMs announce what they're about to do instead of doing it. The meta-commentary slows the writing down and gives it a tutorial-script feel.

**Before:**
> Let's dive into how caching works in Next.js. Here's what you need to know.

**After:**
> Next.js caches data at several layers: request memoization, the data cache, and the router cache.

---

## Drafting Scaffolding Left In

Three patterns with one cause: the model worked something out and left the working in the text. Each of them answers a question the reader never asked, and each of them is the fossil of a decision rather than a statement about the subject.

They're worth checking as a group. Where one shows up, the others usually do.

### 37. Answering Objections No One Raised

**Phrases to watch:** This isn't (mainly/really) about, I'm not saying/arguing, To be clear, Don't get me wrong, This is not to say, You could argue this differently but, Some might say... but

**Problem:** A defense against a challenge that appears nowhere in the document. The giveaway is that the thing being denied is never discussed anywhere else — the text rules out an interpretation the reader was never offered.

Remove only the unsupported defense. If it contains a real claim, state that claim directly. Keep an objection when the text names who raised it, or answers it in full.

**Before:**
> This isn't mainly about prompt length, and I'm not arguing that documentation doesn't matter. You could categorize the problem another way, but the issue is whether the agent can use the instruction when it acts.

**After:**
> The issue is whether the agent can use the instruction when it acts.

---

### 38. Rejecting Fake Alternatives

**Phrases to watch:** A tempting option/approach would be, One might be tempted to, An obvious approach would be, You might think... but, It would be easy to just, Some would suggest

**Problem:** An option no reader would have considered, introduced and dismissed in the same sentence, then never mentioned again. Usually this is an earlier draft's reasoning surviving into the final text. Cut the fake option and state the real constraint.

One rejected option can be legitimate. Several short, unrelated rejections in a row is the pattern. For each one, ask what a reader learns that the next sentence doesn't already tell them.

**Before:**
> Session tokens are rotated every 24 hours. A tempting approach would be to rotate them by restarting the auth service on a cron job, but that would drop every active session. Rotation happens in place, and clients refresh transparently.

**After:**
> Session tokens are rotated every 24 hours, in place, and clients refresh transparently.

**Acceptable (leave it alone):** a design doc, ADR, or tutorial where the rejected option is one a reader would genuinely reach for, and the rejection is the point.

---

### 39. Writing About the Previous Version

**Problem:** Documentation that describes the change instead of the behavior. Whoever reads it next doesn't know what "the previous approach" was and doesn't care. Describe what the thing does now.

The exception is documents that are *about* change: changelogs, release notes, migration guides, ADRs, upgrade instructions. There, the previous version is the subject.

**Before:**
> This function was added to replace the previous approach of iterating through all items, which caused O(n²) performance.

**After:**
> This function uses a hash map for O(1) lookups, avoiding the O(n²) cost of naive iteration.

---

## What Not to Flag

None of the following is evidence on its own. Several patterns in one passage is evidence; one of these is a coincidence.

- **Perfect grammar and consistent style:** Plenty of people write well, and plenty of text has been edited. Polish is not a tell.
- **Mixed casual and formal register:** Often just a technical writer, or someone young, or someone playful, or a document several people touched.
- **Bland or robotic prose:** AI writing has *specific* traits. Dryness without those traits is a dry writer.
- **Formal or academic vocabulary:** §7 is a list of particular words. It does not extend to every long word, and it does not license simplifying prose that's supposed to be formal.
- **Transition words in isolation:** "Additionally," "Moreover," "Consequently." Once meaningful, now not — piled up they still read badly, but one of them proves nothing.
- **Curly quotes alone:** See §22. Usually a Mac.
- **Em dashes alone:** See §17. Journalists and essayists use them heavily, and most current models now use them less than professionals do.
- **One short sentence for emphasis:** A fragment is a tool. A row of them is a pattern.
- **A heading joining two topics with "and":** "Costs and benefits," "Setup and teardown." See §27. The tell is a heading that withholds its own answer, not one that names two things.
- **Deliberate repetition:** Anaphora is centuries old. Change a repeated opening only when the repetition isn't doing anything.
- **"Honestly" or "look" mid-sentence:** Ordinary in speech and casual writing. The tell is the staged pause as an opener, not the word.
- **Real scope notes, disclaimers, and caveats:** Keep legal and safety notices, genuine corrections, known limitations, named objections, and FAQ answers.
- **Real alternatives:** Keep the options a reader would actually weigh. See §38.
- **Correct, complex formatting:** Templates and editors produce clean output.
- **Secondhand text:** Never rewrite a watched phrase inside a quotation, a title, a proper name, or an example where the phrase is being discussed rather than used. This document is full of sentences that would fail its own checks.

There's a deeper version of this warning. These patterns are signs of a problem, not the problem. Removing the signs from genuinely bad writing just makes it bad writing that's harder to spot. If the underlying text is vague, unsupported, or wrong, fixing the vocabulary doesn't help.

---

## Human Details to Keep

These carry the writer's voice. Removing them is the most common way an edit overshoots.

- **Specific, unusual detail:** A real address, an odd quote, "the lawyer who used to work upstairs from my dentist." Generated text smooths these into generalities; don't finish the job.
- **Mixed feelings and unresolved tension:** "I think this was mostly the right call, but it still bothers me that we found out by breaking them, and I can't say why that distinction matters." Note the tension with the voice table in `SKILL.md`, which cuts emotional processing: the difference is whether the feeling is attached to something. A specific reservation about a specific decision is the writer thinking. "I genuinely don't know how to feel about this one," with no referent, is a hook. Keep the first, cut the second.
- **Dated, era-bound references:** Slang, memes, in-jokes that pin to a year and a subculture. Models lag by a year or more.
- **Deliberate first-person choices:** A cut or a word the writer could defend.
- **Variety in sentence length:** Real writing alternates. Generated text settles into an even mid-length cadence, and an aggressive edit can flatten a human document into that same cadence.
- **Genuine asides and self-corrections:** "(I keep wanting to say 'almost' here, but it really was certain.)" Models rarely interrupt themselves.

---

## No Longer Reliable Tells

Some patterns that used to be strong AI tells have largely aged out as models changed. Don't treat their *absence* as proof of human authorship, and don't hunt for them as priorities:

- **Didactic disclaimers** ("It's worth noting that this is a complex topic with many perspectives") — still worth cutting as filler, but no longer a distinctive AI signature. Common in 2022–2024 output.
- **Section summaries** ("In summary," "In conclusion," a trailing "Conclusion" heading that restates the document) — a strong tell when models were asked to "write an article" in 2023–2024. Still bad writing when it says nothing; no longer a signature. §35 covers the version that's still worth cutting.
- **Explicit prompt-refusal text** ("As an AI language model, I can't...") — rare in pasted content now.
- **Abrupt mid-sentence cutoffs** from token limits — much less common, and a bad paste does the same thing.
- **Stale access dates** in citations — an article written in 2026 citing sources "accessed" in 2024. Newer models seldom do this, and there are innocent explanations.
- **Most of §7's vocabulary** — "Delve" and "tapestry" are period pieces at this point. See the era buckets in that section.

These move over time. See the README's upgrading section for how to keep this catalog current against the source.
