# Connect the app to your Google Sheet (once, about 10 minutes)

Students' results are stored in a Google Sheet on your own Google account. Only you can read them; each student
can see only their own pairing result.

1. Open https://sheets.new and name the sheet **ECO 414 Games Results**.
2. Click **Extensions > Apps Script**. Delete everything in the editor and paste the whole of `Code.gs` (this folder).
3. On the first line of code, change `CHANGE-ME-to-a-long-secret` to your own **lecturer key**: a long phrase that is
   hard to guess, for example three or four random words. Keep the quotation marks. Click **Save** (disk icon).
4. Click **Deploy > New deployment**. Click the gear next to *Select type* and choose **Web app**.
   - Description: `ECO 414 games`
   - Execute as: **Me**
   - Who has access: **Anyone**

   Click **Deploy**, then **Authorize access** and choose your account. Google warns that the app is unverified
   because you wrote it yourself: click **Advanced > Go to … (unsafe)** and **Allow**.
5. Copy the **Web app URL** (it ends in `/exec`).
6. Open the app (https://zingdavid.github.io/eco414-games/), click **Lecturer** at the bottom, paste the URL and your
   lecturer key, and click **Save and test**. Then create your first session.

The sheet fills itself: tab **Sessions** (one row per session), **Responses** (one row per student answer) and
**Outcomes** (pairing results and earnings).

Tip: send the Web app URL (not the key) to be built into the app. The join QR code then gets shorter, and students
who type the session code can join without having scanned a QR code first.

## Changing the script later

Edit the code, save, then **Deploy > Manage deployments > edit (pencil) > Version: New version > Deploy**.
The URL stays the same. If you change the lecturer key, enter the new key in the app's lecturer **Settings**.
