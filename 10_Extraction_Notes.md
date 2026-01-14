<!-- @format -->

# 10_Extraction_Notes.md

This document records empirical findings from working with the sample PDF corpus. Those findings informed the initial extraction rules (regex patterns) seeded in the schema (see the `field_parsing_rules` seed data in `05_Schema.md`).

Non-normative: this file explains _why_ the initial rules look the way they do. The executable truth is the seeded rules in `05_Schema.md`.

---

## document_name

**What we observed**

- The submission/trade name is typically present near the beginning of the document in a labeled form.
- Label text is not perfectly consistent in capitalization and punctuation, and may contain non-word separators.

**Why the rule is shaped this way**

- The optional `Trade/` prefix reflects observed label variants.
- `\W*` is used to tolerate colons, dashes, or multiple spaces after the label.
- The rule captures the remainder of the line because the name frequently contains spaces and mixed characters.

Seed rule:

- `^(?:Trade/)?document Name\W*(?P<value>.+)$`

---

## k_number

**What we observed**

- The K-number appears in at least two common contexts:
  1. explicitly labeled as “510(k) Number”
  2. embedded in a reference line such as “Re: K######”
- The identifier format is consistent: `K` followed by six digits.

**Why the rule is shaped this way**

- The alternation `(?:510\\(k\\) Number|Re:)` covers the observed labeling patterns.
- The strict `K\\d{6}` constraint reduces false positives from other “K”-like tokens.

Seed rule:

- `^(?:510\\(k\\) Number|Re:)\\W*(?P<value>K\\d{6}).*$`

---

## regulation_number

**What we observed**

- Regulation numbers appear in a labeled field and are expressed as a decimal form (e.g., `870.4200`).
- The label is stable enough in the corpus to use as an anchor.

**Why the rule is shaped this way**

- `\\d+\\.\\d+` captures the stable decimal structure while allowing variable digit counts.
- Anchoring on the label avoids accidentally capturing other decimal numbers in the document.

Seed rule:

- `^Regulation Number\\W*(?P<value>\\d+\\.\\d+).*$`

---

## regulation_name

**What we observed**

- The regulation name is typically presented as a labeled field near the regulation number.
- The value is free text and may include punctuation.

**Why the rule is shaped this way**

- Capturing the remainder of the line is appropriate because the regulation name is not structurally constrained.
- `\W*` tolerates separators after the label.

Seed rule:

- `^Regulation Name\W*(?P<value>.+)$`

---

## regulatory_class

**What we observed**

- Regulatory class appears as a labeled field and is written as “Class” followed by a Roman numeral.
- The “Class …” expression is consistent in the corpus.

**Why the rule is shaped this way**

- `Class\\s+[IIVX]+` captures the canonical representation while constraining to expected values.
- Anchoring on the label reduces collisions with narrative mentions of class elsewhere.

Seed rule:

- `^Regulatory Class\\W*(?P<value>Class\\s+[IIVX]+).*$`

---

## product_codes

**What we observed**

- Product codes appear as one or more short alphanumeric identifiers.
- The label is sometimes singular or plural: “Product Code” vs “Product Code(s)”.
- Values may be comma-separated and may contain spaces.

**Why the rule is shaped this way**

- `\\(s\\)?` handles the observed singular/plural label variation.
- `[A-Z0-9,\\s]+` captures comma-separated lists with optional whitespace.
- The character class is deliberately conservative (uppercase letters + digits) to avoid capturing narrative text.

Seed rule:

- `^Product Code\\(s\\)?\\W*(?P<value>[A-Z0-9,\\s]+).*$`

---

## manufacturer_name

**What we observed**

- The legal entity name appears under multiple possible labels depending on the PDF template:
  - Sponsor
  - Applicant
  - Manufacturer
  - Submitter Name
- In some samples, the label-based line is absent or unreliable, but the entity name still appears as a standalone line with a corporate suffix.

**Why the rules are shaped this way**

- The primary rule uses a label alternation to cover observed headings without needing multiple separate rules.
- The fallback rule matches common legal suffixes to catch cases where the labeled field is missing and the entity appears in a “letterhead-like” form.
- The fallback is intentionally looser and should be lower priority than the labeled rule.

Seed rules:

- `^(Sponsor|Applicant|Manufacturer|Submitter Name)\\W*(?P<value>.+)$`
- `^(?P<value>.+?(?:Inc\\.?|LLC|Ltd|S\\.r\\.l\\.|S\\.A\\.|GmbH))$` (fallback)

---

## Notes on corpus-driven tuning

- The rules favor **high recall within the sample corpus** while remaining reasonably constrained to reduce obvious false positives.
- “First match wins” + priority ordering was chosen because the corpus shows a small number of stable patterns per field, and deterministic behavior is more valuable than exhaustive extraction in the POC.
- When the corpus expands, the expected adjustment mechanism is to add new rules with appropriate priority rather than modifying code.
