# Brain setup (owner only, once, about 5 minutes)

The shared brain is a Google Sheet you own. Exec members never touch it directly and need no
accounts: the agent talks to it through a web link plus a shared key.

1. Go to sheets.google.com and create a blank sheet named **NOBE Outreach Brain**.
2. In the sheet: **Extensions > Apps Script**. Delete what is there, paste all of
   `server/Code.gs`, and click Save.
3. In the function dropdown at the top pick **setup**, click **Run**, and approve the
   permissions (it is your own script). Open **Execution log**: copy the **Shared key**.
4. **Deploy > New deployment**. Gear icon > **Web app**. Set:
   - Execute as: **Me**
   - Who has access: **Anyone**

   Click **Deploy** and copy the **Web app URL** (ends in `/exec`).
5. Put the URL in `config/nobe.json` as `"brain_url"`, commit, and push. That URL is safe to be
   public: nothing works without the key.
6. Send the **shared key** to exec privately (text or Slack DM, never in the repo). The installer
   asks for it.

Check it: `python3 tools/brain.py sync` should print `brain: 0 contacts`.

**Changing the key** (someone leaves exec): Apps Script > Project Settings > Script Properties >
edit `KEY`, then send the new key to current exec. Old installs stop working until they update
`brain.key`.

**Updating Code.gs later:** paste the new code, then Deploy > Manage deployments > edit (pencil)
> Version: New version > Deploy. The URL stays the same.
