# Pilot review

Four full recordings were processed: Reality 101 episode 1 (two-speaker conversation), The CTO Show #107 (interview), Mortal Steel episode 1 (fiction with music), and Developer Commentary 1 (solo speech). The fourth replaced an initially misclassified solo candidate and remains part of the original 85-recording inventory, with no repeat submission.

Twelve source extracts cover the beginning (70 seconds), middle (35 seconds), and end (40 seconds) of each recording. They were crosschecked locally using Whisper small.en, independently of ElevenLabs. Normalized token sequence agreement ranged from 89.4% to 99.4%. This measures agreement between two fallible models, not word accuracy against ground truth. Direct auditory review is unavailable in this session.

Inspected passages contain coherent introductions, middle discussion/scenes and closing passages. No large missing speech passage was apparent from the sampled crosschecks. Fillers and false starts are retained. Speaker counts were 2 for Reality 101, 2 for the CTO interview, 4 for the fiction, and 1 for the solo commentary; labels are provisional and no speaker identity was assigned.

Known review issues:

- Reality 101 introduces Steven as “Stephen Schrimbeck” in the machine text. The verified catalog spelling is Steven Schrembeck. Original words are retained without silent correction.
- Mortal Steel's opening word “Mortal” is assigned 9.08–49.64 seconds by Scribe. The local recognizer instead places it around 49.08–49.74 seconds, following the music. This is a clear alignment candidate for review; raw timestamps are preserved.
- Dramatic voices and narration can be merged into one speaker label. Names in fiction also vary in spelling. Neutral labels and original text are retained.

Decision: proceed with machine transcription, attach review flags, and keep human correction/listening status explicitly incomplete. Searchable preservation transcripts are useful with these documented limitations. No corrected editions have been created.

See pilot-crosschecks.json for excerpts, timings and independent model output, and pilot-plan.json for parameters and the review gate.
