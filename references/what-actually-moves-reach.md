# What actually moves reach

Measured 2026-08-22 off the live public endpoint, 12 most recent `@billy.coder`
posts. Re-measure before trusting any number here.

```bash
curl -s -H 'X-IG-App-ID: 936619743392459' \
  "https://www.instagram.com/api/v1/users/web_profile_info/?username=billy.coder"
```

Account at time of measurement: **2,916 followers, 83 posts.**

---

## 1. The finding that reorganises everything

| Posted | Views | Likes | Comments | comment/view |
|---|---:|---:|---:|---:|
| Aug 8 | **89,480** | 3,977 | **1,949** | 2.18% |
| Aug 10 | **68,591** | 4,401 | **1,477** | 2.15% |
| Aug 12 | 6,683 | 339 | 132 | 1.98% |
| Aug 17 | 1,045 | 26 | 28 | 2.68% |
| Aug 18 | 147 | 2 | 1 | 0.68% |
| Aug 18 | 413 | 16 | 9 | 2.18% |
| Aug 18 | 790 | 24 | 6 | 0.76% |
| Aug 19 | 136 | 8 | 23 | **16.91%** |
| Aug 19 | 143 | 10 | 1 | 0.70% |
| Aug 20 | 521 | 27 | 24 | 4.61% |
| Aug 20 | 2,206 | 121 | 29 | 1.31% |
| Aug 21 | 89 | 3 | 4 | 4.49% |

Two posts hold **92.8% of the views and 93.0% of the comments** of the last
twelve. The nine since Aug 17 average **610 views and 13.9 comments**.

**The comment rate is flat.** Account mean **2.16%**. The 89k reel converted at
2.18%. The 89-view reel converted at 4.49%, which is *better*. The winners did
not persuade harder. They were simply shown to more people.

So: **the funnel below the impression is not the problem and has never been the
problem.** The CTA works, the keyword mechanic works, the comment ask works. The
only variable that has ever moved is **how many people the first three seconds
were served to**. Do not spend another build tuning the ask.

## 2. What separated the two that got served

Classified from each post's own caption and opening frames:

| Class | Example | Result |
|---|---|---|
| Named angry third party + physical object | "Flock is going to be pissed someone open sourced the blueprint" | **89,480** |
| Forbidden knowledge + hardware | "Leaked: military grade radar, open sourced" | **68,591** |
| Named institution + physical object | "NASA gave away the plans to a Mars rover" | 6,683 |
| Named company, no physical object | "Meta charges you per message" | 1,045 |
| Physical object, no named party | flatbed scanner as a material scanner | 2,206 |
| No name, no object | "Your DMs are a password manager" | 89 |

The gradient is monotonic across all twelve. **A name someone could be angry
about, and a thing you can point a camera at.** Software that only exists in a
terminal is the bottom of this table every single time.

Opening frames of the two winners, measured off the downloaded files:

|  | 89k | 68k | Aug 21 (89 views) |
|---|---|---|---|
| Scene cuts (thresh 0.25 / 0.4 / 0.6) | 9 / 4 / 3 | 4 / 2 / 2 | 1 |
| Audio at 0.1s | -17.0 dBFS | -17.5 dBFS | **-64.6** |
| Opens on | camera shaken off a pole until it bursts | radar dish, fireball at 0.5s | blurred laptop |
| Footage | real world | real world | rendered HTML |
| Banner | one line, frame 0, never changes | same | none for 2s |
| Presenter | absent 3s+ | late, small inset | full frame immediately |
| Length | **54.17s** | 13.44s | 22.03s |

**Length did not separate them.** 54.17s and 13.44s both won. Treat the 20s
ceiling as a habit, not a law, and never as a reason to cut a real-world beat.

**The nine flops are better made than the two hits.** Craft was never the
variable.

## 3. The outlier worth chasing

Aug 19, 136 views, **23 comments, 16.91%** - eight times the account mean. Topic
was a person sending 69 job applications they did not write. Personal stake,
first person, a number about a human rather than a repo. Reach failed, intent
did not. **That is the highest-converting idea the account has produced.** It is
worth reshooting against a real-world opener rather than writing off.

## 4. Off-account research, 2026 (web sources, pulled 2026-08-22)

Flagged: this folder is Skool-only. These were pulled on explicit instruction.

Things to build toward, all reported as positive drivers:

- **Watch time is the #1 ranking signal**, counted as total seconds including
  replays. A 15s reel watched three times outranks a 60s watched once. So a
  reel built to be rewatched beats a reel built to be long.
- **DM shares are the strongest engagement signal**, above saves, above
  comments, with likes now the weakest. Something a viewer wants to send to one
  specific person outranks something they want to praise. "Flock is going to be
  pissed" is exactly a send-to-a-friend sentence. Write the hook so it names the
  person it should be sent to.
- **Faces inside the first 3 seconds: +35% retention** in the general data. This
  account's own two winners have **no face for 3s+**. When the general data and
  the account data disagree, the account data wins. Read this as: something
  alive and moving in the first 3 seconds, which a face is one cheap way to get
  and real-world destruction is a better one.
- **Trending audio inside the first 3 seconds: +41% retention.** The account
  currently ships synthesised beds and gets zero of this lift. Worth one test.
- **Captions raise completion**, reported at 80% more likely to finish, and 60%
  say on-screen text improves enjoyment. Already done, keep doing it.
- **Pattern interrupts** - a cut, zoom, angle change or new text every few
  seconds - hold the eye. The winners do cut: 9 cuts in 54.29s and 4 in 13.56s
  at threshold 0.25. But BC-020 cuts at **0.045/s** against the 89k reel's
  **0.17/s**, so cut rate does not separate them either way. What changes inside
  the frame is real-world motion, and that is the interrupt that matters here.
- **Curiosity gap / open loop.** Viewers seek closure; an unresolved question
  creates the tension that keeps them there. Resolve too fast and they leave,
  too slow and they leave. The account's ask is a closure device, so put the
  gap in line 1 and close it at the CTA, not in the middle.
- **Density drives rewatch.** Information moving faster than one pass can absorb
  makes people watch again, and replays count as watch time.

## 5. What to do with all of this

In order, highest leverage first:

1. **Gate the topic before anything is built.** Run
   `scripts/topic_gate.py`. Under the pass mark, do not shoot it.
2. **Open on the real world with sound at frame 0.** Something physical, moving,
   audible on the first frame. Never a blurred laptop, never a rendered page,
   never silence.
3. **Name the party who would be angry**, in the caption and in line 1.
4. **Hold one declarative banner from frame 0**, unchanged. Both winners do this.
5. Only then worry about the edit.

## 6. Measured off the two winners directly, 2026-08-22

Pulled with `pull_reference.py` and decoded with `decode_reference.py`. These are
the files as Instagram serves them, 720x1280.

| | 89k reel | 68k reel |
|---|---|---|
| runtime | 54.29s | 13.56s |
| frame 0 dBFS RMS at 0.1s | **-17.0** | **-17.5** |
| integrated | -14.99 LUFS | -14.47 LUFS |
| true peak | **-0.01 dBTP** | **-0.40 dBTP** |
| cuts at thresh 0.25 | 9 (0.17/s) | 4 (0.30/s) |
| words | 163 at 3.00 w/s | 29 at 2.14 w/s |
| background | #0c0e12 | #0c0e12 |

### The rules our own skill bans, that both winners break

This is uncomfortable and it is measured, so it goes in the file.

- **They say the word "free".** Both, in the delivered audio: "free on GitHub".
  The 68k reel also burns it on screen: `Military grade radar, 20 km, multiple
  targets, free`.
- **They name GitHub.** The 68k reel's banner reads
  `Open Sourced Military Grade Radar Just Dropped on GitHUb`, held from frame 0,
  **including that typo**, for the whole first half. 68,609 views.
- **They show the repo page.** Stars, forks, the Star button, the notification
  bell, the project's own System Architecture diagram, all clearly legible.
- **They say the star count.** "23,000 stars, and it comes with a system
  architect." On screen: `23.5k stars   5.4k forks`.
- **They master over the peak ceiling.** -0.01 and -0.40 dBTP against a spec of
  under -1.

**The one thing they do NOT show is the repo's name.** The GitHub capture is
scrolled so the `owner/repo` header sits above the top of frame. Verified by
cropping the full resolution frame at the cut.

So the gate is not "hide GitHub". The gate is **hide the name and nothing else**.
Everything else - the platform, the stars, the licence, the word free, the
architecture diagram - is *proof*, and proof is what makes someone comment to get
the name. The rule as written was over-broad and it cost us the proof beat.

Do not read this as permission to relax the ban on the repo NAME. That one is the
whole business.

### What they actually look like

Real world, shot outdoors: ocean, mountains, rocks, a real radar dish on a
tripod, and **two real explosions**, one on frame 0 and one on the last beat. The
presenter is a **small inset strip along the bottom**, not a full-frame matte.
The 89k reel opens `This repo probably shouldn't exist` and is episode three of a
named series.
