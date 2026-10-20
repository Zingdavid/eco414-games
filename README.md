# ECO 414 Classroom Games: Ultimatum and Dictator

An app for running the Ultimatum and Dictator games in class. **No internet is needed during the class**, and
there is no server: every computer or phone works on its own, and the lecturer collects the results.

Online version (for installing on phones and computers): https://zingdavid.github.io/eco414-games/

## Two ways to play

| Mode | How it works | Best for |
|---|---|---|
| **Play on my own** (strategy method) | Each student makes three decisions: an Ultimatum offer, the smallest offer they would accept, and a Dictator gift, plus a guess of the class average. The lecturer's device later pairs everyone at random and works out earnings. | Lab computers or phones, one student per screen |
| **Play with a partner** | Two students share one screen. A offers, B sees the offer and accepts or rejects; then B plays the Dictator Game. | Showing a live rejection |

At the end each student sees a short **code** (for example `S-TAWONGA-450-300-200-500-1000`) and a QR code.

## Installing on the lab computers

**Option A: no internet at all (USB stick).** Copy `ECO414 Games (offline).html` and `install_lab.bat` to a USB
stick. On each computer, double-click `install_lab.bat`: it puts **ECO414 Games** on the desktop. Open it with
Chrome or Edge. The file holds everything it needs.

**Option B: install as an app (needs internet once).** On each computer, open
https://zingdavid.github.io/eco414-games/ in Edge or Chrome and click **Install** in the address bar (Edge: ... >
Apps > Install this site as an app). It then opens from the Start menu and works offline.

Phones: open the same link and choose **Add to Home screen** / **Install app**.

## Live results on the lecturer's laptop (local network, no internet)

1. Double-click `run_games_server.bat` on the lecturer's laptop. A window shows the **student address** (for example
   `http://192.168.1.23:8080`) and your **lecturer PIN**; the lecturer page opens by itself (`http://localhost:8080/lecturer`).
   The first time, the window asks you to **choose a PIN** (4 to 8 digits); it is saved in `pin.txt` and used every
   time after that. To change it, delete `pin.txt` and start the server again.
   The first time, Windows also asks whether Python may use the network: tick **Private networks** and click **Allow**.
2. Enter the PIN. The **Students join** tab shows a big QR code and the address: put it on the projector.
3. Students on the same lab network or Wi-Fi (or the laptop's mobile hotspot) open that address in any browser;
   nothing needs to be installed on their computers. Results are sent to the laptop as soon as each student finishes.
4. Students never see the results. The lecturer page updates every 3 seconds; **Present to class** shows the results
   full-screen for the projector, without names.
5. The stake set on the lecturer page applies to every student. Results are also saved in `results\` (one file per
   session), so nothing is lost if the window is closed by mistake; **Data > Clear** starts a new session.

If the lab network blocks connections between computers, use the methods below (scan, files or paste) instead.

## Running a class (without the server)

1. Tell students the stake if it is not the default MWK 1,000 (students can change it under *change*).
2. Students choose **Play on my own**, enter a nickname or student number and make their decisions.
3. Collect the codes on the lecturer's laptop or phone (click **Lecturer** at the bottom of the page):
   - **Scan**: *Start camera* and point it at each screen's QR code (a phone works well for walking round a lab);
   - **Files**: students click *Save as file* into a shared network folder or USB stick, then you select all the files;
   - **Paste**: students send their codes (for example on WhatsApp) and you paste the whole batch.
4. **Class results** shows the distribution of offers and gifts, the acceptance curve and beliefs. **Match and
   pay** pairs players at random and shows each person's earnings. **Data** downloads a CSV for the tutorial.
5. Students click **Next player** before leaving so the next class starts clean.

Collected results stay in the browser of the device that collected them; download the CSV after class.
Lab computers that are reset at restart will lose any saved data, so collect before shutting down.

## For maintenance

Edit `src/app.html`, then run `python build.py`. It writes `docs/` (the online app) and the single offline file.
Change `CACHE` in `build.py` on every update so installed copies refresh. Libraries in `vendor/`:
qrcode-generator 1.4.4 (Kazuhiko Arase, MIT) and jsQR 1.4.0 (Cosmo Wolfe, Apache-2.0).
