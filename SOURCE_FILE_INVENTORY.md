# SOURCE FILE INVENTORY
Project folder: `VCP By TheChayyy` (Google Drive, user's Mac)
Scan performed: 2026-09-04. Folder is flat (no subdirectories, no hidden files).

| # | Filename | Type | Size | Modified | Readable? | Relevant? |
|---|----------|------|------|----------|-----------|-----------|
| 1 | SCANNER N FUNDAMENTAL INK.txt | Text | 103 B | 2023-09-11 | Yes (fully read) | Yes — screener links |
| 2 | vcp example.pdf | PDF (image-only, 20 pages) | 631,840 B | 2023-09-08 | Yes (all 20 pages visually inspected) | Yes — core visual examples |
| 3 | vcp workshop.pdf | PDF (image-only, 46 pages) | 64,745,719 B | 2023-09-11 | Yes (all 46 pages visually inspected) | Yes — PRIMARY strategy source (full workshop slide deck) |
| 4 | september vcp workshop day 1.mkv | Video, 1920x1080, h264/aac | 856,335,734 B | 2023-09-11 | Visual: fully inspected (46 scene-change frames). Audio: NOT available (see note below) | Yes — confirmed to re-present Source A's slide deck live, plus incidental live-chart/tool context (Source D in SOURCE_KNOWLEDGE_MAP.md) |
| 5 | workshop day 2.mkv | Video, 1920x1080, h264/aac | 825,134,615 B | 2023-09-11 | Visual: fully inspected (58 scene-change frames). Audio: NOT available (see note below) | Yes — a distinct "Day 2 Special Class" live stock-screening/tool-usage demo, including the full Chartink ATR screener formula (Source E in SOURCE_KNOWLEDGE_MAP.md) |
| 6 | FNO GIFT SWING WALE IGNORE THIS.mkv | Video, 1920x1080, h264/aac, 246.2s (~4.1 min) | 82,168,022 B | 2023-10-30 | Yes (staged, transcribed) | User's own filename explicitly says "IGNORE THIS" — different subject (F&O/GIFT Nifty swing trading, not equity VCP). See Section on this file for content summary and disposition. |

## Note on file #6 (FNO GIFT SWING WALE IGNORE THIS.mkv)
Fully staged and inspected (246-second / 4.1-minute screen recording, 1920x1080, h264/aac). Speech could not be reliably transcribed (see technical note below), but 2 representative frames were extracted via scene-change detection and visually reviewed. Content: an OBS Studio recording-setup screen and a TradingView chart of SARVESHWAR FOODS LTD with green horizontal consolidation-zone boxes in the same visual style as `vcp example.pdf`, plus a watchlist showing NIFTY/BANKNIFTY/index futures alongside individual equities. The clip appears to be an unfinished/discarded recording take (it shows the OBS control panel itself, not a clean explanation) rather than deliberate teaching content. Consistent with the user's own filename ("IGNORE THIS"), this file is **excluded from STRATEGY_MASTER.md** — noted here for traceability but not treated as a strategy source. No rules were extracted from it.

## Technical note on files #4 and #5 (resolved)
Both videos exceed the 400MB single-file transfer limit between the user's computer and this environment. The user ran ffmpeg on their own machine to produce compressed audio tracks (`day1_audio.mp3` 86.8MB, `day2_audio.mp3` 55.5MB — NOT transcribed, see below) and scene-change-triggered frame captures (`day1_frames/`: 46 JPEGs, `day2_frames/`: 58 JPEGs — ALL visually inspected via the Read tool).

**Audio: not transcribed.** This environment's network access is restricted to package registries (pypi, npm, github raw). Every speech-to-text avenue was tried and failed: `openai-whisper`/`faster-whisper` need model weights from Hugging Face/Azure/GitHub-release-CDN (all HTTP 403 here); hosted APIs (OpenAI, Groq, Deepgram, AssemblyAI) are equally unreachable; the one offline pip-bundled option (`pocketsphinx`) was tested against the "IGNORE THIS" clip's audio and produced verified, unusable, semantically meaningless output — so it was deliberately not used on the two main videos to avoid fabricating a transcript. Anything said aloud in these videos that is not also visible on-screen is NOT captured anywhere in this knowledge base.

**Visual: fully inspected.** All 104 extracted frames (46 + 58) were read and analyzed. Day 1 re-presents the identical Source A slide deck live (no new slide content) plus incidental live-chart/tool-browsing context. Day 2 is a distinct "Special Class" live stock-screening/tool demo that revealed, among other things, the full filter logic of the Chartink "ATR" screener already referenced by URL in Source C. See SOURCE_KNOWLEDGE_MAP.md, Sources D and E, for the complete findings, including two items explicitly flagged UNKNOWN/UNCONFIRMED (a locally-saved `ADANIPOWER_...pdf` file whose content never rendered in the sampled frames, and a "mid cap momentum based model" phrase whose relationship to the core VCP strategy could not be determined without audio).

## No other files found
No spreadsheets, Word documents, screenshots (outside the PDFs), or additional text files exist in this folder. No subfolders exist.
