# ICS Phisher

**ICS Phisher** is a tool for generating and sending realistic `.ics` calendar invites for use in **red team simulations**, **blue team awareness**, and **employee phishing training**. It allows researchers and defenders to better understand how phishing via calendar invites works in real scenarios.

> ⚠️ **Disclaimer**: This tool is intended strictly for educational and authorized testing purposes. Unauthorized use is prohibited.

---

## Purpose

ICS Phisher helps simulate phishing attacks by crafting and optionally sending `.ics` calendar invites that mimic services such as:
- Google Meet
- Zoom
- Microsoft Teams
- Outlook

These invitations can contain links to attacker-controlled infrastructure (for training), allowing security teams to observe detection capabilities and improve awareness training.

---

## How It Works

The tool generates `.ics` files (calendar invites) with embedded HTML email bodies that resemble legitimate meeting invites. Two modes are supported:

- `generate`: Generates the `.html` and `.ics` files but does not send them.
- `auto`: Generates the files and sends them via SMTP to the target recipient(s).

Templates are used to control how the HTML email body looks. These templates reside in the `templates/` folder and support variable placeholders.

---

## Folder Structure

```
ics-phisher/
├── templates/       # HTML templates (Zoom, Google Meet, Teams, etc.)
├── payloads/        # Generated .ics and .html files
├── ics_phisher.py   # Main script
```

---

## Template System

Templates are stored as `.html` files in the `templates/` directory and must use the following placeholders:

- `{{attacker_url}}` – URL the victim will be redirected to.
- `{{organizer_name}}` – Name of the meeting organizer.
- `{{organizer_email}}` – Email of the meeting organizer.
- `{{summary}}` – Meeting title.
- `{{description}}` – Meeting description.
- `{{start}}` – Start time (as `YYYY-MM-DD HH:MM`).
- `{{end}}` – End time (as `YYYY-MM-DD HH:MM`).

You can create your own templates and just place them in `/templates`. They will be automatically detected.

---

## ⚙Parameters

| Parameter          | Description |
|--------------------|-------------|
| `--mode`           | Required. `generate` or `auto`. Use `auto` to send the email via SMTP. |
| `--start`          | Required. Start time of the meeting (format: `YYYY-MM-DD HH:MM`). |
| `--end`            | Required. End time of the meeting. |
| `--organizer-name` | Required. Organizer's name. |
| `--organizer-email`| Required. Organizer's email address. |
| `--description`    | Required. Meeting description text. |
| `--summary`        | Required. Meeting subject. |
| `--recipient`      | Required. Comma-separated recipient email(s). |
| `--attacker-url`   | Required. URL used as the phishing/training link. |
| `--template`       | Required. HTML template to use (e.g., `zoom.html`). |
| `--output-prefix`  | Optional. Filename prefix for generated files. |
| `--smtp-server`    | SMTP server address (required in `auto` mode). |
| `--smtp-port`      | SMTP port (default: 587). |
| `--smtp-user`      | SMTP username (optional). |
| `--smtp-pass`      | SMTP password (optional, blank password allowed). |
| `--sender`         | Required in `auto` mode. Sender email (From:). |

---

##  Usage

### Generate Files Only
```bash
python ics_phisher.py --mode generate --start "2025-07-20 10:00" --end "2025-07-20 11:00" \
    --organizer-name "Alice" --organizer-email "alice@example.com" --summary "Zoom Call" \
    --description "Monthly Zoom Sync" --recipient "victim@example.com" --attacker-url "http://evil.com" \
    --template zoom.html
```

### Generate and Send Automatically
```bash
python ics_phisher.py --mode auto --smtp-server smtp.example.com --smtp-user smtpuser \
    --smtp-pass smtppass --sender phishing@example.com --start "2025-07-20 10:00" \
    --end "2025-07-20 11:00" --organizer-name "Alice" --organizer-email "alice@example.com" \
    --summary "Zoom Call" --description "Monthly Zoom Sync" --recipient "victim@example.com" \
    --attacker-url "http://evil.com" --template zoom.html
```

---

## Real-World Training Use

This tool is perfect for:
- **Blue teams** to test detection of calendar-based phishing.
- **Security awareness programs** to train employees on suspicious invites.
- **Red team engagements** to simulate modern phishing techniques.
- **Mature organizations** that want to practice full kill-chain scenarios.

---

## Scalability

- Add as many `.html` templates as you want in the `templates/` folder.
- Reuse the same logic and variables to simulate new platforms.

---

## Author

**Created by:** *q3alique*  
**Version:** 1.0

---

## License

Use responsibly. For authorized use only. Distributed for research and education purposes.
