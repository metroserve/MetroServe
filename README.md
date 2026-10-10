# MetroServe Final Prototype

A polished Django prototype for municipal issue reporting and service tracking.

## Included
- MetroServe dark/blue/teal visual system with responsive animations.
- Citizen registration/login using email + password.
- Citizen dashboard, profile photo upload and notifications.
- Report issue workflow with browser GPS/current-location button, manual location fallback and photo upload.
- Automatic department routing and unique MET-YYYY-##### reference numbers.
- Real QR code generated for every complaint; QR opens public tracking page.
- Public complaint tracking without citizen login.
- Municipal staff login, command center, queue, assignment, status updates and resolution notes.
- Reports dashboard and CSV export.
- Django admin branding and UserProfile image support for administrators.

## Setup
```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py shell
```

In the shell, seed departments:
```python
from complaints.models import Department
for name in ['Water & Sanitation','Roads & Infrastructure','Electricity','Waste Management','Traffic & Transport','Community Services']:
    Department.objects.get_or_create(name=name)
```
Then:
```python
exit()
python manage.py runserver 0.0.0.0:8000
```

For phone testing on the same Wi-Fi, set `PUBLIC_BASE_URL` in `config/settings.py` to the computer's LAN URL, for example `http://192.168.1.113:8000`.

Browser GPS requires permission and is normally restricted to secure contexts (HTTPS) or localhost. On a LAN demo, some browsers may block geolocation. The form always keeps manual location entry as a fallback.

## Hero image and logo
Put the final assets in:
- `static/images/logo.png`
- `static/images/hero.jpg`

The supplied CSS uses a working text mark until the final logo is added.
