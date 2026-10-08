---
title: Frost Window: 30 years of weather and a laptop-sized Gemma tell you what to do outside this week
published: true
tags: devchallenge, hf26challenge, opensource, ai
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)*

## What I Built

Every October, gardeners in cold places ask the same question: how many weekends are left before the first frost? The answer decides whether you dig up the basil this Saturday, whether it is time to put garlic in the ground, and whether that hike should happen now or next spring.

Most apps answer with a single "average first frost" date. An average hides the thing you actually care about, which is risk. A town whose average is November 10 can still freeze on October 30 one year in ten.

**Frost Window** gives you the risk, then gets out of the way:

1. You type a place name.
2. It pulls 30 years of daily low temperatures for that spot from the free Open-Meteo archive.
3. It works out, for every one of those years, the last spring frost and the first fall frost.
4. It turns that into four plain sentences: the chance of frost by next week, the typical and the early first frost, whether it is bulb-planting season, and the date seedlings are safe next spring in 9 of 10 years.
5. A small open-weight model, Gemma 3 4B running locally through Ollama, turns those sentences into a four-line "go do this outside" plan.

Here is the real output for Seoul, run on October 8:

```
Facts:
- No frost in the next 7 days in any of the past 30 years.
- Typical first frost is in about 32 days (Nov 10); an early year is Oct 30.
- This is garlic and tulip planting season.
- Next spring, frost-tender seedlings are safe outside after Apr 12 in 9 of 10 years.

This week's outdoor plan (gemma3:4b, running locally):
Enjoy a hike in Bukhansan National Park, cycle along the Han River, or explore the beautiful gardens of Namsan.
This is perfect garlic and tulip planting season – get those bulbs in the ground!
```

And Minneapolis on the same day, where the picture is very different:

```
Facts:
- Frost by next week happened in 27% of past years.
- Typical first frost is in about 16 days (Oct 24); an early year is Oct 10.
- Harvest tender crops (tomatoes, basil, peppers) soon.
- This is garlic and tulip planting season.
```

The screen part takes about thirty seconds. Everything it suggests happens outdoors.

## Demo

Live page with eight cities (Seoul, Minneapolis, London, Toronto, Denver, Sapporo, Berlin, Melbourne), all generated on my machine with the same code:
https://lottolove5131-lang.github.io/frost-window/

To run it for your own town:

```bash
ollama pull gemma3:4b
python frost_window.py "Your Town"
```

It needs only the Python standard library.

## Code

{% github lottolove5131-lang/frost-window %}

## How I Built It

The design rule was simple: **the model never decides when frost comes.**

Frost dates come from counting, not from generation. `frost_dates()` walks each complete year of daily minimums and records the last day at or below 0 °C before July and the first one after July. Percentiles over those 30 values give the "typical", "early year" and "safe in 9 of 10 years" dates. That part is about forty lines and you can check it by hand.

`facts()` then converts the numbers into short sentences with a few rules ("if the median first frost is under three weeks away, say harvest tender crops"). Only those sentences go to Gemma, with an instruction to use them and nothing else. Gemma's job is the part language models are good at: turning dry facts into something friendly, and picking a local park or river to suggest.

Three things broke along the way, and fixing them improved the tool more than any prompt tweak:

- **The 1B model invented places.** With `gemma3:1b`, Seoul got a "Moon Valley" walk that does not exist. Moving to `gemma3:4b` fixed it: Bukhansan, the Han River and Namsan are all real. It costs about 35 seconds per plan on a CPU-only laptop, which is fine for a weekly plan.
- **The model contradicted the data.** My first prompt sent the raw JSON, and the 1B model wrote about "frosty air" in a week where frost had never happened in 30 years. Pre-digesting the numbers into sentences stopped that.
- **The Southern Hemisphere was upside down.** Melbourne's "first fall frost" came out in July, because my season logic assumed fall starts in July. The code now shifts the calendar by half a year for negative latitudes. Then a second problem showed up: frost at Melbourne's city coordinates happened in only one of the last 30 years, and the tool was reporting that single cold night as a "typical" date. It now says "Frost is rare here" when frost occurs in fewer than half the years, instead of pretending a pattern exists.

Stack: Python standard library, Open-Meteo geocoding and historical archive APIs, Ollama, Gemma 3 4B. The demo page is one static HTML file reading a JSON file.

## Why Does Open Innovation Matter?

Three reasons, all concrete for this project:

- **It costs nothing to run.** No API key, no account, no billing page. A garden club, a school, or a hiking group can run it on whatever laptop is in the room.
- **The weather data is open, so the numbers are checkable.** Anyone can pull the same 30 years from Open-Meteo and confirm the frost dates. That matters more than the prose: a frost date you cannot verify is just a guess with confidence.
- **The model is swappable and stays on your machine.** If `gemma3:4b` is too slow on an old laptop, `--model gemma3:1b` works, and I documented exactly how it fails. If a better small model ships next month, it is a one-word change. Nothing about where you live leaves your computer except the coordinates sent to the weather archive.

A closed API would have made the friendly part slightly more polished. It would also have made the tool cost money, need a key, and depend on a service that can change under it. For a tool meant to be used once a week by people who would rather be outdoors, open was the better fit.

## Prize Categories

- Best Use of Gemma

*AI disclosure: I built this with help from an AI coding assistant, which wrote much of the code and drafted parts of this post with me. All outputs shown are real runs of the published code.*
