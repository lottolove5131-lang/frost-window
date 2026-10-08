# Frost Window

**When will it frost where I live, and what should I go do outside this week?**

Frost Window answers that from 30 years of daily low temperatures for any place on Earth, then asks a small open-weight model (Gemma, running on your own laptop through Ollama) to turn the numbers into four short lines of "go outside" advice.

No account. No API key. No cloud model. The only network calls are to the free, open Open-Meteo weather archive.

## What it tells you

```
$ python frost_window.py "Seoul" --model gemma3:4b

Facts:
- No frost in the next 7 days in any of the past 30 years.
- Typical first frost is in about 32 days (Nov 10); an early year is Oct 30.
- This is garlic and tulip planting season.
- Next spring, frost-tender seedlings are safe outside after Apr 12 in 9 of 10 years.
```

The numbers come from plain arithmetic, not from the model:

- **Last spring frost / first fall frost** for each of the past 30 years (daily low at or below 0 °C, change it with `--threshold`).
- **Median** and an **early year** (10th percentile) for the first fall frost.
- **"Safe in 9 of 10 years"** date for planting out tender seedlings next spring (90th percentile of the last spring frost).
- **Chance of frost by next week**, counted across the 30 years.

The model only writes the friendly part. It is told to use those facts and nothing else, so it never decides when frost comes.

## Run it

```bash
# 1. Install Ollama (https://ollama.com) and pull a Gemma model
ollama pull gemma3:4b      # or gemma3:1b on a small laptop

# 2. Run (Python 3.9+, standard library only)
python frost_window.py "Your Town"
python frost_window.py "Minneapolis" --model gemma3:1b
python frost_window.py "Seoul" --no-llm        # numbers only, fully offline after the fetch
```

Options: `--years` (default 30), `--threshold` in °C (default 0; use -2 for a hard freeze), `--model`, `--no-llm`.

## How it works

1. Open-Meteo geocoding turns the place name into coordinates.
2. Open-Meteo historical archive returns daily minimum temperatures for the past 30 years.
3. `frost_dates()` finds the last spring and first fall frost for every complete year.
4. `facts()` turns the percentiles into sentences (rules, not AI).
5. `plan()` sends only those sentences to Gemma via the local Ollama API.

## Data and credits

- Weather: [Open-Meteo](https://open-meteo.com/) historical weather API (CC BY 4.0).
- Model: Google Gemma 3, run locally with [Ollama](https://ollama.com/).

## License

MIT
