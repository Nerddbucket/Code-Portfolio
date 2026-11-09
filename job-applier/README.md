# Job applier

This is one project in the portfolio. Java labs, Python labs, and this app share `scripts/setup.sh` at the repo root. Run that once, then use the steps below for this project only.

One button on your own computer. It reads the public Greenhouse, Lever, and Ashby job feeds you list, then files an application only when your config can answer every required question. It sends your resume PDF unchanged.

It skips a job when a required answer is missing, when a visible CAPTCHA or login wall is on the page, or when the site asks for an email code. It does not solve CAPTCHAs, and it does not guess.

## What you fill in

Copy `config.example.json` to `config.json`.

1. Profile. Name, email, phone, country, city, LinkedIn, GitHub, portfolio, work authorization (`yes` or `no`), sponsorship (`yes` or `no`), salary floor, and earliest start date (`YYYY-MM-DD`). Veteran status and EEO answers default to `decline`. Put school and AWS certification text in `extra_answers`. Leave an answer blank if you do not want that question answered; the job is then skipped when the question is required.
2. Search. Job title phrases, locations (`Remote`, `North Carolina`, or a city), seniority (`entry`, `mid`, `senior`, `staff`, `manager`, `intern`), include and exclude keywords, and how old a listing can be. `North Carolina` also matches Raleigh, Durham, Charlotte, Cary, Chapel Hill, Greensboro, and Winston-Salem. `daily_cap` is how many applications one day may send. The app will not send more than 50 in a day.
3. Resume. `resume_pdf` is a path to your PDF. The file is uploaded as-is.
4. Company boards. These are the names in the public career URLs, not the whole URL:
   - Greenhouse: `https://job-boards.greenhouse.io/gitlab` → `gitlab`
   - Lever: `https://jobs.lever.co/spotify` → `spotify`
   - Ashby: `https://jobs.ashbyhq.com/ashby` → `ashby`

`submit` stays `false` until you want Start to send applications. With `submit` false, Start is a dry run: it lists what it would file and sends nothing.

`privacy_consent` and `certify_truth` let Start check the application-processing and "this information is true" boxes. `marketing_consent` stays false, so newsletter boxes are not checked. A required box that is neither of those skips the job.

Set `cover_letters` to `claude` only if `ANTHROPIC_API_KEY` is set in the environment. If Claude is missing, the app uses a short template made from your name and links. The key stays in the environment, not in `config.json`.

## Run it

Python 3.11 or newer.

```bash
cd job-applier
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m applier
```

Open http://127.0.0.1:8765

- **Practice run** files one sample application to this computer and skips a job with an unknown question, a visible CAPTCHA, the wrong seniority, the wrong location, and an old listing. Nothing is sent to an employer.
- **Start dry run** reads your boards and does not send.
- **Start filing** sends when `submit` is true and the profile is complete. **Stop** prevents the next submit.

The first live run will skip more jobs than it sends. That is the config doing its job. Add a phrase under `extra_answers` when you see a required question you are willing to answer the same way every time.
