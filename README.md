# ECO 414 Classroom Games: Ultimatum and Dictator

App: https://zingdavid.github.io/eco414-games/

An installable app for running the Ultimatum and Dictator games in class. It **works offline**: answers are saved on
the device and sent automatically when it is next online. Results go to **your Google Sheet** (or, with no internet
at all, to your laptop), you pair the class with one click, and each student sees their own earnings.

## How a class runs

1. **Lecturer:** open the app, click **Lecturer** (bottom of the page), create a **session** (title, amount to divide,
   steps). Put the **Students join** tab on the projector: it shows a QR code and a 4-character session code.
2. **Students:** scan the QR code with the phone camera (or open the app and type the code), enter their name, and make
   four choices: an Ultimatum offer, the smallest offer they would accept, a Dictator gift, and a guess of the class
   average. They check their answers and submit. No internet? The app says *Saved on this device* and sends the
   answers later by itself.
3. **Results** updates as answers arrive. **Present to class** shows them full-screen, without names.
4. **Pair and pay** pairs everyone at random (each student proposes to one classmate and responds to another; the
   Dictator Game uses a new random pairing) and works out earnings. Students open **My results** to see what their
   partner offered or gave and what they earned. They never see who their partner was.
5. **Data** downloads a CSV. Everything is also in the Google Sheet.

**Play with a partner on this device:** two students share one screen and see a real offer and a live accept or
reject. Their result is synced the same way.

**Devices that never get online:** the student's screen shows a backup code and QR code; the lecturer scans or pastes
it under **Add codes**.

## Setting up

- **Google Sheet (once):** follow `backend/SETUP.md`.
- **Installing on phones and lab computers:** open the app link once while online and choose **Install** (Chrome or
  Edge: install icon in the address bar; phones: *Add to Home screen*). After that it opens from the home screen or
  Start menu and works offline. A computer that can never go online can use `ECO414 Games (offline).html` from a USB
  stick (`install_lab.bat` puts it on the desktop); results from it are collected with backup codes.

## No internet at all: the laptop server

`run_games_server.bat` turns the lecturer's laptop into the server. Students on the same Wi-Fi, lab network or the
laptop's hotspot open the address it shows (or scan the QR code on the **Students join** tab); nothing needs to be
installed. The lecturer page asks for your PIN (chosen the first time; delete `pin.txt` to change it). Results are
saved in `results\data.json`. Everything else (sessions, results, pairing, My results) works the same.

## Maintenance

Edit `src/app.html`, then `python build.py` (writes `docs/` and the offline file). Change `CACHE` in `build.py` on every
update so installed copies refresh. `backend/Code.gs` is the Google Sheet backend; `server.py` implements the same API
for the laptop. `backend/mock_gas.js` runs `Code.gs` under Node for testing. Libraries in `vendor/`: qrcode-generator
1.4.4 (Kazuhiko Arase, MIT) and jsQR 1.4.0 (Cosmo Wolfe, Apache-2.0).
