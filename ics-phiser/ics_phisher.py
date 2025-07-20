#!/usr/bin/env python3

import os
import argparse
import datetime
import uuid
import re
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.encoders import encode_base64
from email.utils import formatdate

from colorama import init, Fore, Style
init(autoreset=True)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, "templates")
PAYLOAD_DIR = os.path.join(SCRIPT_DIR, "payloads")
os.makedirs(PAYLOAD_DIR, exist_ok=True)

VARIABLE_PATTERN = r"{{(.*?)}}"

def list_templates():
    return sorted(f for f in os.listdir(TEMPLATE_DIR) if f.endswith(".html"))

def resolve_html_template(template_name, variables):
    path = os.path.join(TEMPLATE_DIR, template_name)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for key, value in variables.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    unresolved = re.findall(VARIABLE_PATTERN, content)
    if unresolved:
        print("[!] Warning: Unresolved placeholders:", unresolved)
    return content

def get_unique_filename(base_name, ext):
    path = os.path.join(PAYLOAD_DIR, f"{base_name}.{ext}")
    counter = 1
    while os.path.exists(path):
        path = os.path.join(PAYLOAD_DIR, f"{base_name}_{counter}.{ext}")
        counter += 1
    return path

def format_ical_datetime(value):
    dt = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M")
    return dt.strftime("%Y%m%dT%H%M%SZ")

def build_ics_content(summary, description, organizer_name, organizer_email, start, end, recipients):
    dtstamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    uid = str(uuid.uuid4())
    dtstart = format_ical_datetime(start)
    dtend = format_ical_datetime(end)

    attendees_block = ""
    for email in recipients:
        attendees_block += (
            f"ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;"
            f"PARTSTAT=NEEDS-ACTION;RSVP=TRUE;CN={email}:mailto:{email}\n"
        )

    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//phisher//EN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{summary}
DESCRIPTION:{description}
ORGANIZER;CN={organizer_name}:mailto:{organizer_email}
{attendees_block.strip()}
SEQUENCE:0
STATUS:CONFIRMED
TRANSP:OPAQUE
END:VEVENT
END:VCALENDAR"""
    return ics

def send_email(sender, recipients, subject, html_file, ics_file, smtp_server, smtp_port, smtp_user=None, smtp_pass=None, template_name=None):
    try:
        recipients_list = [r.strip() for r in recipients.split(",")]

        with open(html_file, 'r') as f:
            html_body = f.read()
        with open(ics_file, 'r') as f:
            ics_content = f.read()

        msg = MIMEMultipart('mixed')
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ", ".join(recipients_list)

        # Apply Microsoft-specific headers if template is Teams/Outlook
        if template_name and any(x in template_name.lower() for x in ['teams', 'outlook']):
            msg.add_header("X-MS-Exchange-Organization-AuthAs", "Internal")
            msg.add_header("X-MS-Exchange-Organization-AuthSource", "EXCHANGE-SERVER")
            msg.add_header("X-MS-Exchange-Organization-CalendarBooking", "true")
            msg.add_header("X-MS-Exchange-Organization-MessageDirectionality", "Originating")

        # Construct message body
        part_html = MIMEText(html_body, "html")
        part_ics_inline = MIMEText(ics_content, 'text/calendar; method=REQUEST; charset=UTF-8')

        msg_alternative = MIMEMultipart('alternative')
        msg_alternative.attach(part_html)
        msg_alternative.attach(part_ics_inline)
        msg.attach(msg_alternative)

        # Attach ICS as a file
        ics_attach = MIMEBase('application/ics', ' ;name="invite.ics"')
        ics_attach.set_payload(ics_content)
        encode_base64(ics_attach)
        ics_attach.add_header('Content-Disposition', 'attachment; filename="invite.ics"')
        msg.attach(ics_attach)

        print("[*] Connecting to SMTP server...")
        with smtplib.SMTP(smtp_server, int(smtp_port), timeout=10) as server:
            server.ehlo()
            if server.has_extn("STARTTLS"):
                try:
                    server.starttls()
                    server.ehlo()
                    print("[+] STARTTLS successfully negotiated.")
                except Exception as e:
                    print(f"[!] Failed to start TLS: {e}")
            else:
                print("[!] STARTTLS not supported — continuing without encryption.")

            if smtp_user:
                try:
                    server.login(smtp_user, smtp_pass or "")
                    print("[+] SMTP authentication successful.")
                except smtplib.SMTPAuthenticationError:
                    print("[-] SMTP authentication failed — check credentials.")
                    return

            server.sendmail(sender, recipients_list, msg.as_string())
            print(f"[+] Email sent to: {', '.join(recipients_list)}")

    except Exception as e:
        print(f"[!] Error sending email: {e}")

from colorama import init, Fore, Style
init(autoreset=True)

def print_custom_help(available_templates):
    print(Fore.BLUE + Style.BRIGHT + "\n📅 ICS Phisher — Realistic Calendar Phishing Generator")
    print(Fore.WHITE + Style.NORMAL + "Version: " + Fore.CYAN + "1.0" + Fore.WHITE + " | Author: " + Fore.CYAN + "q3alique")
    print(Fore.WHITE + "Description: " + Style.NORMAL + "Creates realistic-looking calendar invites using ICS (.ics) files and HTML emails.\n"
          "             Useful for blue team exercises, phishing simulations, and awareness training.\n")

    print(Fore.WHITE + Style.BRIGHT + "🟨 Usage:")
    print("  python ics_phisher.py --mode <generate|auto> --template <name> [other options]\n")

    print(Fore.WHITE + Style.BRIGHT + "🔹 Required Arguments:")
    print(f"  {Fore.CYAN}--mode{Style.RESET_ALL:<21} 'generate' (just create files) or 'auto' (create and send email)")
    print(f"  {Fore.CYAN}--start{Style.RESET_ALL:<20} Event start time in 'YYYY-MM-DD HH:MM' format")
    print(f"  {Fore.CYAN}--end{Style.RESET_ALL:<22} Event end time in 'YYYY-MM-DD HH:MM' format")
    print(f"  {Fore.CYAN}--organizer-name{Style.RESET_ALL:<11} Display name of the meeting organizer (e.g., Alice)")
    print(f"  {Fore.CYAN}--organizer-email{Style.RESET_ALL:<10} Email address of the organizer (e.g., alice@example.com)")
    print(f"  {Fore.CYAN}--recipient{Style.RESET_ALL:<16} Comma-separated list of recipient emails")
    print(f"  {Fore.CYAN}--summary{Style.RESET_ALL:<18} Title of the event (e.g., Quarterly Sync Meeting)")
    print(f"  {Fore.CYAN}--description{Style.RESET_ALL:<14} Event description shown in invite")
    print(f"  {Fore.CYAN}--attacker-url{Style.RESET_ALL:<13} The URL to embed in the email (e.g., phishing site)")
    print(f"  {Fore.CYAN}--template{Style.RESET_ALL:<17} Template name to use for HTML formatting")

    print(Fore.WHITE + Style.BRIGHT + "\n🔹 Optional Arguments:")
    print(f"  {Fore.CYAN}--output-prefix{Style.RESET_ALL:<12} Base filename for saved .ics and .html files (default: payload)")
    print(f"  {Fore.CYAN}--smtp-server{Style.RESET_ALL:<14} SMTP server to send the email (required for 'auto' mode)")
    print(f"  {Fore.CYAN}--smtp-port{Style.RESET_ALL:<16} SMTP port number (default: 587)")
    print(f"  {Fore.CYAN}--smtp-user{Style.RESET_ALL:<16} Username for SMTP authentication (optional)")
    print(f"  {Fore.CYAN}--smtp-pass{Style.RESET_ALL:<16} Password for SMTP (optional)")
    print(f"  {Fore.CYAN}--sender{Style.RESET_ALL:<19} Email address used in the 'From:' field (required for auto mode)\n")

    print(Fore.GREEN + "🟩 Examples:")
    print("  python ics_phisher.py --mode generate --start '2025-07-20 10:00' --end '2025-07-20 11:00' \\")
    print("      --organizer-name 'Alice' --organizer-email 'alice@example.com' --summary 'Zoom Call' \\")
    print("      --description 'Monthly Zoom Sync' --recipient 'victim@example.com' --attacker-url 'http://evil.com' \\")
    print("      --template zoom_invite.html\n")
    print("  python ics_phisher.py --mode auto --smtp-server smtp.example.com --smtp-user smtpuser \\")
    print("      --smtp-pass smtppass --sender phishing@example.com --start '2025-07-20 10:00' --end '2025-07-20 11:00' \\")
    print("      --organizer-name 'Alice' --organizer-email 'alice@example.com' --summary 'Zoom Call' \\")
    print("      --description 'Monthly Zoom Sync' --recipient 'victim@example.com' --attacker-url 'http://evil.com' \\")
    print("      --template zoom_invite.html\n")

    print(Fore.YELLOW + Style.BRIGHT + "📂 Available Templates:")
    for t in available_templates:
        print(f"  - {t}")
    print()

def main():
    available_templates = list_templates()

    if "-h" in sys.argv or "--help" in sys.argv:
        print_custom_help(available_templates)
        return

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--mode", choices=["generate", "auto"], required=True, help="generate (only files) or auto (send email too)")
    parser.add_argument("--start", required=True, help="Start time (YYYY-MM-DD HH:MM)")
    parser.add_argument("--end", required=True, help="End time (YYYY-MM-DD HH:MM)")
    parser.add_argument("--organizer-name", required=True)
    parser.add_argument("--organizer-email", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--recipient", required=True)
    parser.add_argument("--attacker-url", required=True)
    parser.add_argument("--template", required=True, help=f"HTML template (available: {', '.join(available_templates)})")
    parser.add_argument("--output-prefix", default="payload")
    parser.add_argument("--smtp-server", help="SMTP server")
    parser.add_argument("--smtp-port", default="587", help="SMTP port")
    parser.add_argument("--smtp-user", help="SMTP username (optional)")
    parser.add_argument("--smtp-pass", help="SMTP password (optional)")
    parser.add_argument("--sender", help="Sender email (used as From:)")

    args = parser.parse_args()

    if args.template not in available_templates:
        print("[-] Invalid template. Available templates:", ", ".join(available_templates))
        return

    if args.mode == "auto":
        if not args.smtp_server or not args.sender:
            print("[-] --smtp-server and --sender are required in auto mode.")
            return

    if args.smtp_user and args.smtp_pass is None:
        print("[*] Warning: --smtp-user provided without --smtp-pass. Attempting login with blank password.")

    recipient_list = [email.strip() for email in args.recipient.split(',')]

    html_vars = {
        "attacker_url": args.attacker_url,
        "organizer_name": args.organizer_name,
        "organizer_email": args.organizer_email,
        "summary": args.summary,
        "description": args.description,
        "start": args.start,
        "end": args.end
    }

    html_body = resolve_html_template(args.template, html_vars)
    ics_body = build_ics_content(
        summary=args.summary,
        description=args.description,
        organizer_name=args.organizer_name,
        organizer_email=args.organizer_email,
        start=args.start,
        end=args.end,
        recipients=recipient_list
    )

    html_path = get_unique_filename(args.output_prefix, "html")
    ics_path = get_unique_filename(args.output_prefix, "ics")

    with open(html_path, "w") as f:
        f.write(html_body)
    with open(ics_path, "w") as f:
        f.write(ics_body)

    print(f"[+] HTML saved to {html_path}")
    print(f"[+] ICS saved to {ics_path}")

    if args.mode == "auto":
        send_email(
            smtp_server=args.smtp_server,
            smtp_port=args.smtp_port,
            smtp_user=args.smtp_user,
            smtp_pass=args.smtp_pass,
            sender=args.sender,
            recipients=args.recipient,
            subject=args.summary,
            html_file=html_path,
            ics_file=ics_path,
            template_name=args.template
        )

if __name__ == "__main__":
    main()
