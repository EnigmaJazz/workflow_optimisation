# Gemini API advisor route — RETIRED

The Google API advisor route was retired because Google API quota is nearly exhausted and its
carriers were redundant with `advisor-spec-pre` and `advisor-spec-post`.

The retired agents were `advisor-gemini-pre`, `advisor-gemini-post`, and
`advisor-gemini-evidence`. Their definitions are recoverable from git at `d0c4a76^`.

Evidence gathering now lives in `advisor-evidence` (`opencode-go/qwen3.8-flash`), which retains the
sandbox-only advisor surface.

No remaining setup or credential step is required for this retired route.
