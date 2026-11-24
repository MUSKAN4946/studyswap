# AI Assistance Disclosure

This project was built with help from an AI assistant (Claude, made by Anthropic). This file explains what the assistant did and what I did myself.

## What the AI assistant helped with

- Explained the project brief and the four cases that must be handled.
- Suggested the tech stack (Python, FastAPI, SQLite) and the folder structure.
- Wrote the first versions of the code files, the SQL schema (including the capacity trigger and the unique index), the seed script, and the documentation text (README, entity diagram, API contract, evidence log).
- Guided me step by step through the setup, the Git commands and the GitHub push.

## What I did myself

- Set up the project folder, virtual environment and installed the packages on my own computer.
- Created every file and folder, pasted the code into the files, and ran the app.
- Ran the seed script and started the server.
- Tested the four mandatory cases by hand through the Swagger page (`/docs`) and the browser: the rejected fourth booking, the booking for a session that does not exist, the duplicate booking, and the restart test. I also tested cancelling and booking again.
- Took every screenshot in the `screenshots/` folder from my own runs. No result in the evidence log was invented.
- Created the GitHub repository and pushed the work. I also found that my commits showed the wrong author name, and fixed it so the commits show my own account.

## What I did not verify

- I have not tested many simultaneous requests at the same moment. The evidence log says so.
- I have not run the README on a second, clean computer yet.

## Other sources

All data is fictional. Aliases such as `owl42` are made up. No real names, emails, student numbers or passwords are used anywhere in this project.

This disclosure is written to describe the work honestly as it was done. Anything I did not check is listed above as written.