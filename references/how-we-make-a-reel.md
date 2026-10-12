# How we make a reel

Written to hand to somebody who wants to run this system on their own account.
It is the actual process behind @billy.coder, not a cleaned up version of it.
Everything in here is free. No paid API, no subscription, no stock library.

The account went from 79 to 669 followers on one reel built this way. What did
it was the topic and the shape, not the polish, and that is the single most
important thing on this page.

---

## What we are actually making

| | |
|---|---|
| **Length** | 15 to 20 seconds. Never longer. |
| **Frame** | 1080 x 1920, 30fps, vertical, full bleed |
| **Audio** | 48 kHz stereo, mastered to -14 LUFS, true peak under -1 dBTP |
| **Voice** | one person, phone camera, chest up, talking straight to camera |
| **On screen** | real footage or a live graphic at all times, plus burned captions |
| **Ending** | one uppercase word, and a promise to send something if they comment it |

The whole thing is a funnel. Views are not the product. **A comment is the
product**, because the comment triggers an automated DM that delivers the thing
we promised, and that DM is where the audience actually gets built.

Everything below exists to protect that one mechanic.

---

## The four beats every reel follows

1. **A named paid thing loses.** "DocuSign is $50 a month." "Higgsfield is $20 a
   month." A price the viewer recognises, said out loud in the first five
   seconds.
2. **Proof on a real screen.** Not a mockup, not a slide. Actual footage of the
   thing working. This is the part most people skip and it is the part that
   makes the difference between a like and a comment.
3. **The presenter, cut out.** No box, no border. Segmented from the background
   and composited over the footage, so a face and the evidence share the frame.
4. **One word.** "Comment VET and I will send you the setup."

If a reel is not landing, it is almost always beat 1 or beat 2 that is missing.

---

## The rules that never move

These are not style preferences. Each one is a lesson that cost a post.

> Superseded 2026-08-22: show the proof, hide only the `owner/repo` name. See SKILL.md.

**Never name the tool or show the repo.** Not in the audio, not on screen, not
in a URL, not in a terminal prompt. If the viewer can find it themselves they
have no reason to comment, and the comment is the whole business model. We have
shipped a reel with a repo name visible on one frame and it flattened the
comment count. Blur it, mask it, or shoot around it.

**Never use the word FREE in a hook or a title.** It reads as spam and the
platform treats it that way. Say the licence instead. "Apache 2.0" and "MIT" are
harder claims than "free" anyway, because they are checkable.

**No em dashes, en dashes or double hyphens in anything published.** It is the
single biggest tell that a caption was written by AI, and the audience for this
account is exactly the audience that spots it.

**One unique CTA keyword per post, never reused.** Keep a burned list. Once a
keyword is used it is dead, because the automation routes on it and two posts on
the same keyword send the wrong thing to somebody.

**Never invent a number.** No fabricated savings, no made up results, no fake
scan output. Use the repo's own published figures and verify them the day you
shoot. A single invented statistic in this niche gets picked apart in the
comments and the whole account pays for it.

**Change the colour theme between reels.** Running the same palette on every
post is what makes an account's output blur into one video. Pick the palette
from the subject: a security reel runs red and amber, not the house lime.

**Avoid orange, and avoid purple on dark.** Both are the default AI tool
palette right now and both make a video look generated.

**Apple emoji only.** The Windows and Android glyphs look wrong to an audience
that is almost entirely on iPhone. Keep the real PNGs in a shared assets folder
and make the build fail loudly if one is missing, rather than falling back to a
system font. We shipped the wrong emoji once because the fallback was silent.

**No dead frames.** The reel is under twenty seconds. If the screen is showing a
static plate with nothing moving, that second is wasted. Something is always
happening.

---

## Stage 1: find the topic

The topic does more work than the edit. Getting this right is most of the job.

**Where they come from.** We measure what is already working for competitors in
the same lane, then take the underlying idea, never the wording. Concretely:
search Instagram for a caption sentence from a reel that performed, resolve the
post with `yt-dlp` to pull its real view, like and comment counts, and record it.
This is free and it beats guessing.

**The metric that matters is comments per follower**, not views. A reel with
40k views and 12 comments is a worse model than one with 6k views and 300
comments, because comments are the funnel.

**What qualifies.** For this account, a topic has to be a free and open source
thing that replaces something people currently pay for, and it has to be
provable on a screen. If there is nothing to film, there is no reel.

**What does not.** Explainers. Listicles. News with no CTA. Anything with no
named price, no licence, and nothing on screen to prove it. These get views and
no comments, which is the same as nothing.

**Keep an idea bank and dedupe against it.** We run one in Airtable with the
topics and keywords already burned. Checking it takes ten seconds and stops you
rebuilding a post you already made.

---

## Stage 2: decode a reference

When a competitor's reel performs, pull it apart before writing anything.

Download it, then write down: what is in the first two seconds, where the hook
sits, what is on screen at every beat, what the colour scheme is, how long each
shot holds, where the CTA lands, and what the caption does.

Then decide, explicitly and in writing, **what you are taking and what you are
not**. We keep a short table for this on every recreation. Take the structural
idea, the pacing, the thing that makes it work. Never take the palette, the
wording, the badges, or anything that would let a viewer recognise the source.
The audience must never be able to say this is a copied video.

---

## Stage 3: write the script

**Six lines. That is the format.** Read straight through, briskly, no pauses
between them. We cut the pauses out in the edit anyway.

**Line 1 comes off a hook sheet, always.** Not invented fresh. We work from a
sheet of twenty proven patterns, things like *"This is the truth no one tells
you about ___"* and *"You're probably doing ___ wrong and don't even realize
it."* Offer three options, each a different pattern, and name which pattern each
one is so the person recording can see the framework.

**Lines 2 and 3 are the reel.** This is where the numbers go, and the numbers
have to become the viewer's problem rather than a statistic. The pattern that
works: state the scale, then make it personal. "Somebody checked forty two
thousand of them. One in four had a hole in it. Five percent looked deliberately
malicious. **You install these with one click.**" That last sentence is what
turns a fact into a reason to comment.

**Line 6 is the CTA.** One word, uppercase, never used before.

**Write pronunciations into the script.** "NVIDIA" as *en VID ee uh*. "Apache"
as *uh PATCH ee*. It saves a reshoot.

**Say where the weight sits.** Mark which lines to slow down on and which to
speed through. Pace is the difference between a script that reads fine and a
reel that holds.

---

## Stage 4: record

Ten minutes of phone footage, vertical, chest up, good light.

**The important part is coming back with choices, not one version.** Once the
camera stops you cannot change a single word without another shoot. So the
recording pack always asks for:

- three full takes of the six lines, straight through, no stopping for fumbles
- the hook said three different ways, each from a different pattern
- the CTA line on its own, in case the keyword has to change

We have shipped a reel where only one pass came back, and the CTA keyword was
locked to whatever was said on it. That is a real constraint you inherit for the
life of the post, so spend the extra five minutes.

**Watch the top of frame.** If the top of the head is cropped, no edit fixes it.

---

## Stage 5: build the edit

There are two ways to do this. Pick based on whether you want to write code.

### The simple version, no code

Import to CapCut. Trim to twenty seconds, cut every gap. Add bold high contrast
text overlays out of the top and bottom danger zones. Auto captions on. Export
1080p. This is genuinely fine and it is how the first posts were made.

### The version we actually run

A small Python pipeline per reel, one script per stage, all free and all local.

| Stage | What it does |
|---|---|
| `stt.py` | Word level transcript of the take with **faster-whisper** (`small.en`, CPU). Local, free, gives start and end times per word. |
| `trim.py` | Cuts every pause and any false starts, then speeds the whole take up slightly. Retimes audio and video together so the mouth stays on the words. |
| `matte.py` | Cuts the presenter out of the background using a person segmentation model, and writes a greyscale matte that ffmpeg composites. |
| `theme.py` | Builds the furniture: the persistent banner, the progress bar, the handle, the statement plates. |
| custom renderers | The b-roll. Screen recordings driven by **Playwright**, and animated graphics drawn frame by frame with **Pillow**. |
| `final.py` | Assembles the shots, burns the captions, composites the cutout, mixes the audio, masters it, and copies the result to the delivery folder. |

**Three things about this pipeline that are worth stealing even if you build it
differently:**

**1. Derive the cut from the transcript, never type in timecodes.** Shot
boundaries come from where the speaker actually stops talking, computed from the
word timings. That means changing the pacing re-times the entire edit instead of
sliding every graphic off the word it was cut to. We learned this the hard way:
a grid animation had its colour changes typed in at 1.91s and 3.53s, and the
first speed change would have silently desynced it.

**2. Trim against measured silence, not just the transcript.** Speech to text
word boundaries are loose by up to 0.2 seconds. A trim built only from them can
look clean in the transcript while the audio still has seven tenths of a second
of dead air before the first word. Run silence detection on the audio as well
and cut the union of both.

**3. Master to a number.** -14 LUFS integrated, true peak under -1 dBTP. Measure
it, apply the exact gain needed, then measure again. Instagram normalises audio,
and a reel that is quiet next to the one before it in the feed loses people.

---

## Stage 6: deliver and check

Every finished reel lands in one folder as two files: `NAME.mp4` and a contact
sheet `NAME_SB.jpg` of sixteen frames across the runtime.

**Check the delivered file, not the build log.** This is the rule that catches
the most. A build can report success while the folder still holds an older
render, and we have reported a reel as fixed while the shipped file still had a
repo name visible on it. Pull frames out of the actual delivered mp4, look at
them, and transcribe the delivered audio to confirm nothing was lost.

The contact sheet is for one specific question: **does anything overlap anything
else?** Banner over a caption, caption over the presenter, presenter over the
one graphic that matters. It is the fastest way to catch a collision.

---

## Stage 7: post

Caption shape, every time:

1. Hook line: the named paid product, or the claim
2. What it does, in specifics: stars, licence, price, hardware cost
3. The licence line. MIT, Apache, OSHWA, public domain
4. `Comment X and I'll send it.`
5. A few niche hashtags

Then wire the keyword into the DM automation **before** the post goes up. The
word was said on camera and cannot change, so if the automation is not live the
comments arrive and nothing answers them.

If you post to more than one account through an API, always target by account
ID, never by whatever is default. Ask us how we know.

---

## The traps, ranked by what they cost

**Silently losing audio in ffmpeg.** Two independent filter chains in one
`filter_complex` dropped 3.2 seconds of voice out of the middle of a reel and
nothing errored. Prefer simple `-vf` and `-af` where you can, and always
transcribe the delivered file.

**Trusting the log over the file.** Covered above. It is worth repeating because
it is the one that ships a mistake to an audience.

**Silent asset fallbacks.** A missing emoji fell back to the system font and the
wrong artwork shipped. Make missing assets throw.

**Overlays that hide the evidence.** A persistent banner sat at the top of the
frame for weeks covering the install command, the flagged lines of the file, and
the top of the grid. A banner that hides the thing it is describing is worse
than no banner. Give the furniture a fixed zone and lay the content out
underneath it.

**Pulling b-roll from the competitor's reel.** Check the project's own site or
repo first. The footage is usually there, it is higher quality, and it does not
put somebody else's frame in your video.

**Fake randomness that is not random.** A grid of tiles shuffled with
`(i * 97 + 13) % N` drew visible diagonal stripes. Use a seeded random shuffle so
it looks random and stays identical between rebuilds.

---

## The toolchain

Everything here is free and runs locally on a normal laptop.

- **Python 3** with `Pillow`, `imageio-ffmpeg`, `numpy`
- **faster-whisper** for word level transcription, `small.en` on CPU
- **torch** and **torchvision** for the person segmentation matte
- **Playwright** for screen recordings and screenshots
- **yt-dlp** for pulling reference video and audio
- **ffmpeg**, which comes with `imageio-ffmpeg`
- **Airtable** free tier for the idea bank and the production line
- A DM automation tool for the comment keyword

One note on `yt-dlp` and YouTube: it now needs a JavaScript runtime to solve a
challenge. If you get a 403 on every format, install `yt-dlp-ejs` and point it
at Node with `--js-runtimes node`.

---

## If you only take three things

1. **The topic beats the craft.** A well made video about a boring tool loses to
   a rough video about something people cannot believe is free.
2. **Show the thing working on a real screen.** Proof is the difference between
   a like and a comment, and comments are the only thing that compounds.
3. **Protect the gate.** Never name the tool. The whole system runs on people
   having to ask.
