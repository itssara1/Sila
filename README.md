<div align="center">

# صِلة · Sila
### مهارات تجمعنا · Skills bring us together

**Find your team. Learn from people. Build meaningful connections.**

Arabic / English · Light / Dark · Django

</div>

## Two paths, one community

| Build your team | Learn & teach |
|---|---|
| Publish a hackathon, challenge, or freelance collaboration. | List teaching skills and learning interests. |
| Define roles, seats, and skills before publishing. | Discover people with interest-based suggestions. |
| Review applications, profiles, and consented CVs. | Request learning directly, or offer a skill exchange. |
| Accept members into the team's private conversation. | Open a private conversation after acceptance. |

All collaboration is **unpaid in this version**. Freelance is a project category, not a payment service. Paid opportunities are a future extension. There are no task assignments, work submissions, or payment flows.

## Run locally

Python 3.12 or newer. Validated with Python 3.12.14 and Django 5.2.18.

```sh
git clone https://github.com/itssara1/Sila.git
cd Sila
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Activate on macOS / Linux:

```sh
source .venv/bin/activate
```

Then:

```sh
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000/. `seed_demo` loads skills and fictitious examples. It is safe to repeat. For an empty community, create categories and skills through Django admin instead:

```sh
python manage.py createsuperuser
```

### Local demo accounts

| Username | Demo role |
|---|---|
| `demo_sara` | Leads three teams; teaches Python |
| `demo_noura` | Teaches Figma; interested in Python |
| `demo_ali` | Teaches data analysis; interested in Django |

Password: `SilaDemo123!`. Only run sample data locally. No administrators are created. Use separate browser sessions to try both sides.

## Try the workflows

1. As `demo_noura`, open a team and apply for a designer role.
2. As `demo_sara` in another session, open **My teams → team → Applicants** and accept.
3. Noura sees acceptance in **My applications** and can enter the team conversation.
4. Each further accepted member joins that same room. Pending and rejected applicants have no room access.
5. Open **Learn & teach**, choose a person and skill, and send a request.
6. The recipient accepts in **Learning requests**. Both can enter the private conversation.
7. Learning does not require an offered skill; exchange requests require one of the sender's own teaching skills.

## Profiles and CV privacy

Profiles include a biography, avatar, teaching skills, interests, and an optional portfolio URL. Avatar validation is retained from Skillivity: JPEG/PNG/WebP, 2 MB, maximum 4096px.

CVs are optional PDFs, limited to 5 MB with extension and signature checks. They are not linked publicly. Applicants explicitly consent to sharing with a team leader. An authenticated download view checks authorization. Only avatars are served by the development media route; **never publicly serve `media/private/`** in production. CV downloads return the current uploaded CV rather than a historical attachment.

Leader notes are private. Acceptance updates the application, reserves a seat, prevents duplicate membership, and adds the applicant to the room transactionally. Closing recruitment rejects pending applications and preserves team membership and conversations.

## Identity and fonts

| Element | Color |
|---|---|
| Background | `#FFFFFF` |
| Primary navy | `#172554` |
| Accent lime | `#E4F56A` |

Arabic-first layouts with English switching, responsive forms/cards, and a dark theme saved locally.

CSS uses locally installed **Thmanyah Sans** for UI and **Thmanyah Serif Display** for headings, with Tahoma/Arial fallbacks. The repository **does not distribute, embed, or hotlink their font files**. The current license restricts redistribution and extraction. Install from the official source for local use, or obtain suitable written web-embedding permission before adding webfonts. Other visitors currently see the fallback.

Font source: https://font.thmanyah.com/  
License: https://font.thmanyah.com/licenses

## Structure

```text
accounts/     Custom user, authentication, profile and upload validation
skills/       Bilingual categories and skills
community/    Teams, applications, learning and conversations
support/      Contact form and admin triage
config/       Settings, routing and error handlers
templates/    Arabic/English pages
static/       Sila design, theme, role forms and chat scripts
locale/ar/    Source and compiled translations
```

## Checks

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Automated tests cover page rendering, publishing roles, duplicate/self applications, seats, acceptance and group membership, withdrawal, CV privacy/validation, optional reciprocal learning, recommendations, conversation authorization, message replay, escaped HTML, CSRF, and safe redirects.

## Boundaries and future work

- Chat persists messages and polls every three seconds while the tab is visible. It does not use WebSockets. A UUID prevents retry duplicates.
- Suggestions use learning interests; they do not use AI or require reciprocal skills.
- Teams support up to 12 roles in the publish form, each with 1–20 seats.
- Reapplication to a previously applied role is not enabled.
- This is a local development version, not a production deployment. Configure HTTPS, hosting/database, private media storage, monitoring, abuse controls and account recovery before public release.
- Add explicit compensation terms and separate payment records for paid freelance opportunities in a future version. The current category alone never implies payment.

## Source and author

Built for **Sara Abdullah Alshammari**, based on her Skillivity capstone's authentication, profile and bilingual taxonomy foundation. Sila uses a fresh schema and is not a drop-in database migration for Skillivity. The original repository was read, not modified.

Implementation assistance: OpenAI Codex.
