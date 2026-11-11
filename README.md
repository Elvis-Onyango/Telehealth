# Telehealth

A Django-based telemedicine application with patient and doctor accounts, appointment scheduling, prescriptions, messaging, pharmacy, notifications, and virtual consultations.

## Requirements

- Python 3.10 or later
- Node.js and npm (only needed to rebuild Tailwind CSS)
- PostgreSQL (optional; local development uses SQLite by default)

## Local setup

From the project directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. The default email backend writes messages to the console, and external services such as M-Pesa, Twilio, and Firebase are not required for local startup.

The project loads environment variables from `.env`. For production, set `DJANGO_DEBUG=false`, provide a strong `DJANGO_SECRET_KEY`, configure `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`, and use a production database and email backend. Never commit `.env`. Rotate any real credentials that were previously stored in source control; removing them from the current settings does not remove them from Git history.

### PostgreSQL

The default `DB_ENGINE=sqlite` requires no database server. To use PostgreSQL, set the following values in `.env`:

```dotenv
DB_ENGINE=postgresql
DB_NAME=telemedicine
DB_USER=postgres
DB_PASSWORD=your-local-password
DB_HOST=localhost
DB_PORT=5432
```

The PostgreSQL driver is included in `requirements.txt`.

### Tailwind CSS

To rebuild the project's styles:

```sh
cd theme/static_src
npm ci
npm run build
```

Use `npm run dev` in that directory while developing styles.

### Existing encrypted medical notes

The previous setup used Django's `SECRET_KEY` for medical-note encryption. If you have existing encrypted records, set `DATA_ENCRYPTION_KEY` in `.env` to the same key used by that installation before starting the updated project. Keep this key stable and backed up; changing it makes existing encrypted notes unreadable.

## Project layout

- `apps/users`: accounts, patient and doctor profiles, authentication
- `apps/appointments`: hospitals, appointments, and billing
- `apps/prescriptions`: prescriptions and medical reports
- `apps/messaging`: patient-doctor messaging and WebSocket consumers
- `apps/videoconferencing`: virtual consultation records and meeting links
- `apps/notifications`: notifications
- `apps/pharmacy`: pharmacy and payment integration
- `templates/`, `static/`, `theme/`: Django pages and frontend styles

## Appointment booking

Patients with a completed profile can book at `POST /api/appointments/appointments/` or `POST /api/appointments/`. Provide the doctor ID, date, time, appointment type, and payment preference (`mpesa`, `card`, or `insurance`). The server validates the requested time against configured doctor availability, prevents duplicate bookings, and sets the billing amount from the doctor's consultation fee rather than the browser request. Bookings and billing are created together; payment remains pending because payment-provider checkout is not yet connected.

Authenticated patients and doctors can retrieve their own appointments with `GET /api/appointments/`. The doctor-list and patient-dashboard pages use these endpoints.

Virtual appointments automatically create a Jitsi room. The patient and assigned doctor see a protected “Join video visit” link on their dashboards; the meeting page checks the appointment participants and embeds Jitsi when the scheduled visit begins.

## Hospital administration

Create a Django superuser with `python manage.py createsuperuser`, sign in at `/admin-login/`, and use the Superadmin dashboard at `/api/appointments/superadmin-dashboard/`. Superadmins can create hospitals and provision a hospital administrator account for a single hospital. Hospital administrators can sign in at `/hospital-login/` (or `/admin-login/`) and are sent to `/api/appointments/hospital-dashboard/`; they are not Django staff accounts.

The dashboards manage hospital profiles, doctor assignments and operational profile fields, appointments, and billing status. Hospital administrators only see and manage their assigned hospital. Patient names and contact details are shown only alongside appointments. Clinical notes, prescriptions, medical history, and message content are not included. Appointments are cancelled rather than deleted, billing history is retained, and doctors are unassigned rather than removed. A hospital can only be deleted when it has no linked doctors, appointments, or administrators. Hospital API updates follow the same assignment boundary.

### Local demo data

To add fictional sample hospitals, doctor and patient accounts, appointments, and hospital administrators to a local database, run:

```sh
python manage.py seed_demo_data --password 'user@123'
```

The command is repeatable and does not delete or update unrelated accounts. New demo accounts use the `demo_` username prefix and the supplied password; existing demo account passwords are not reset. This command also creates a demo superadmin. `user@123` is intentionally weak for local demonstration only: do not run this in production or reuse the password elsewhere.

## Patient-doctor messaging

Booking an appointment automatically connects that patient and doctor for messaging; each appointment also has a direct link to open their conversation. The chat page loads contacts and message history over the authenticated REST API, then opens a WebSocket at `/ws/chat/<contact-user-id>/` for live text messages and read receipts. Chat participants can upload files, including prescription documents, and download attachments only after authorization. Structured prescriptions remain managed by the prescriptions API. The access token is passed as a WebSocket subprotocol, not in the URL. Only an active doctor-patient assignment can open or send to a conversation. Local development uses Channels' in-memory layer; deployments with multiple ASGI workers or instances need a shared Redis channel layer for cross-worker delivery. Run the application with its ASGI entry point (`telemedicine_project.asgi:application`) to support WebSockets.

## Private records and notifications

Medical histories and reports are visible to their patient and care-team doctors; prescriptions are visible to the patient and issuing doctor. Patients can create and update their own medical history, while prescription and report creation is restricted to doctors and the patients they care for. Pharmacy orders and payments are scoped to the signed-in user; payment records are read-only through the API, and inventory changes require a Django staff account. Authenticated users can list their own notifications at `GET /api/notifications/` and mark one read with `POST /api/notifications/<id>/read/`.

The patient dashboard summarizes appointments and payment status, medical history, recent prescriptions and reports, pharmacy order history, and notifications. Report attachments download through an authenticated, care-team-scoped endpoint rather than a public media link. Doctor dashboards show their own recent clinical activity, appointment billing status, and notifications. Hospital administrators see appointment and billing summaries plus their own notifications, without access to clinical notes. Pharmacy checkout is still a demo flow; orders and M-Pesa payments are not fully connected to a production checkout process.
