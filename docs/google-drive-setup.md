# Google Drive setup

How to connect the owner's invoice folder to the invoice service. This is
done once, together with the owner, and takes about 20 minutes. Once it is
done, the owner uploads invoices to the folder and **Import invoices** picks
them up (see `invoice-service/README.md`).

## Why a club Google account

The cleanest approach is to **create a dedicated Google account for the club
together with the owner** and set everything up under it: the invoice folder,
the Google Cloud project and the service account.

- **The club owns the setup, not a person.** If it lived under the
  developer's account, the import would stop working the day that account
  is closed or the developer leaves. If it lived under the owner's personal
  account, club data would sit next to their private files.
- **The owner holds the keys.** The owner keeps the password and the
  two-step verification. A developer can be given access and later removed
  without redoing anything.
- **It is reusable.** The same account can later own the accounting sheet
  and anything else the platform connects to.

None of this costs money: a free Google account is enough, and the Drive API
is free at the club's volume (a club's invoice volume). No billing account
is needed.

## What you need

- The owner, in person or on a call. They create the account and approve
  sign-ins on their phone.
- The repository checked out, with the dev stack working
  (`docker compose -f infra/docker-compose.yml up -d --build`).

## Steps

### 1. Create the club Google account (owner)

1. Go to <https://accounts.google.com/signup> and create an account such as
   `<clubname>.invoices@gmail.com`. If the club already uses Google
   Workspace, create a user in the club's domain instead.
2. Use the owner's phone number and a recovery email they control.
3. Turn on **two-step verification**
   (<https://myaccount.google.com/security>).
4. The owner stores the password in their password manager. It never goes
   into the repository, a chat or an email.

### 2. Create the invoice folder (owner)

1. Signed in as the club account, open <https://drive.google.com> and create
   a folder, for example `Invoices`.
2. Share the folder with the owner's personal account as **Editor**, so the
   owner can upload from their phone without switching accounts.
3. Uploads go **directly into this folder**. Subfolders are not read, and
   only PDF, JPEG, PNG and WebP files are imported (Google Docs and other
   files are ignored).

### 3. Create the Google Cloud project

Signed in as the club account:

1. Open <https://console.cloud.google.com>, accept the terms, and create a
   project named e.g. `club-invoices`.
2. Go to **APIs & Services → Library**, search for **Google Drive API** and
   click **Enable**.

### 4. Create the service account and its key

The service account is a robot identity the invoice service signs in as. It
can only see what is shared with it.

1. Go to **IAM & Admin → Service accounts → Create service account**.
2. Name it `invoice-import`. Skip the optional role and access steps: it
   needs no project roles.
3. Copy its email address
   (`invoice-import@<project-id>.iam.gserviceaccount.com`).
4. Open the service account → **Keys → Add key → Create new key → JSON**.
   A `.json` file downloads.
5. Save it as `invoice-service/secrets/drive-service-account.json`, then
   delete the copy in your Downloads folder.

The key is a password. The `secrets/` folder is gitignored; never commit the
key, paste it in a chat or send it by email. If it leaks, delete it under
**Keys** and create a new one.

If key creation is blocked ("Service account key creation is disabled"), the
account is under a Workspace organisation policy. A Workspace administrator
must allow keys for this project
(`iam.disableServiceAccountKeyCreation`).

### 5. Share the folder with the service account (owner)

1. In Drive, open the invoice folder → **Share**.
2. Add the service account's email address as **Viewer**. Untick "Notify
   people" (the robot has no inbox).

Viewer is enough: the service only reads files and never moves, renames or
deletes them. The folder stays the owner's archive.

### 6. Configure the invoice service

1. Copy the folder ID from the folder's URL:
   `https://drive.google.com/drive/folders/<FOLDER-ID>`.
2. Add these two lines to `invoice-service/.env` (copy
   `invoice-service/.env.example` first if the file does not exist):

   ```bash
   INVOICE_DRIVE_FOLDER_ID=<FOLDER-ID>
   INVOICE_DRIVE_CREDENTIALS_FILE=./secrets/drive-service-account.json
   ```

   Both must be set. With only one, the service silently falls back to the
   local inbox (`invoice-service/data/inbox/`).
3. Restart the stack so the new settings are read:

   ```bash
   docker compose -f infra/docker-compose.yml up -d --build
   ```

### 7. Check it works

1. Upload one or two invoices to the folder.
2. In the app, open the invoice review screen and click **Import invoices**.
3. The invoices appear in the queue with the source **Invoice folder**.
4. Click **Import invoices** again: it reports 0 new and downloads nothing.

| What you see | What it means |
| --- | --- |
| "access refused — check that the invoice folder is shared with the service account" | The folder is not shared with the service account email, the folder ID is wrong, or the Drive API is not enabled. |
| "Google Drive credentials file is missing or invalid" | The key is not at `invoice-service/secrets/drive-service-account.json`, or the path in `.env` is wrong. |
| "Google Drive unavailable" | No connection to Google, or Google is having problems. Try again later. |
| The source shows **Local inbox** | The two `INVOICE_DRIVE_*` lines are missing from `invoice-service/.env`, or the stack was not restarted. |
| A file in the folder never appears | It is in a subfolder, is not a PDF/JPEG/PNG/WebP, or is larger than 25 MB. |

## Handing over and removing access

- To give a developer access, the owner adds them as a member of the Cloud
  project (**IAM & Admin → IAM**). To remove it, they delete them there.
- To revoke the import entirely, delete the key under the service account's
  **Keys**, or stop sharing the folder with the service account.
