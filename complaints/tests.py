from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from complaints.models import Complaint


class AssignmentDateTests(TestCase):
    def setUp(self):
        # Create a staff member who can access the staff complaint page.
        self.staff_user = User.objects.create_user(
            username="test_staff",
            password="TestPassword123!",
            is_staff=True,
        )

        # Create a citizen who submitted the complaint.
        self.citizen = User.objects.create_user(
            username="test_citizen",
            password="TestPassword123!",
        )

        self.complaint = Complaint.objects.create(
            citizen=self.citizen,
            issue_type="water",
            title="Water leak",
            location="Test location",
            description="Testing assignment dates.",
        )

        self.submission_date = timezone.localtime(
            self.complaint.created_at
        ).date()

        self.url = reverse(
            "staff_complaint_detail",
            kwargs={"pk": self.complaint.pk},
        )

        self.client.force_login(self.staff_user)

    def test_assignment_date_before_submission_is_rejected(self):
        invalid_date = self.submission_date - timedelta(days=1)

        response = self.client.post(
            self.url,
            {
                "assigned_to": str(self.staff_user.pk),
                "assigned_date": invalid_date.isoformat(),
                "status": "assigned",
                "priority": "normal",
                "resolution_notes": "",
            },
        )

        self.complaint.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.complaint.assigned_date)

    def test_assignment_date_on_submission_day_is_accepted(self):
        valid_date = self.submission_date

        response = self.client.post(
            self.url,
            {
                "assigned_to": str(self.staff_user.pk),
                "assigned_date": valid_date.isoformat(),
                "status": "assigned",
                "priority": "normal",
                "resolution_notes": "",
            },
        )

        self.complaint.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.complaint.assigned_date, valid_date)
        self.assertEqual(
            self.complaint.assigned_to_id,
            self.staff_user.pk,
        )