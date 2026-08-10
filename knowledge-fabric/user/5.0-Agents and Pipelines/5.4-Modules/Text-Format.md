# Text Format (`TEXT_FORMAT`)

Applies **one** text-formatting operation to the upstream output.

**Category:** Utilities · **Deployed:** yes · **Tool-capable:** no

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Input (`in_input`) | Input | The text to transform |
| Output (`out_output`) | Output | The transformed text |

## Properties

**Selector-driven** — choose **Operation** first, then its own fields appear:

| Operation | What it does |
|---|---|
| **Word Count** | Returns the number of words |
| **Case Conversion** | `UPPER`, `LOWER`, or `SWAP` |
| **Text Replace** | Replaces a search string with a replacement |
| **Text Limit** | Truncates to a maximum length |
| **Static Insert** | Inserts fixed text |
| **Text Strip** | Removes surrounding whitespace |

## Use cases

- **Normalising before comparison** — lower-case a value so a Validator's `EQUALS` behaves predictably.
- **Trimming before a model call:** Text Limit caps an oversized upstream value instead of blowing the
  context window.
- **Cleanup:** Text Strip on values read from a file or API.
- **Counting** as a cheap quality signal, feeding a Validator condition.

## Notes

- **One operation per module.** For two transformations, chain two Text Format modules.
- Choose the Operation first — the panel is otherwise nearly empty.
- Deterministic and free. Use it in preference to asking a model to reformat text.
