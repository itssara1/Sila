import uuid
from tempfile import TemporaryDirectory
from django.test import TestCase, override_settings, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils.translation import override
from accounts.models import Profile
from accounts.forms import ProfileForm
from skills.models import Category, Skill
from .models import *


class SilaWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        U = get_user_model()
        cls.leader = U.objects.create_user("leader", password="StrongPass124!")
        cls.alice = U.objects.create_user("alice", password="StrongPass124!")
        cls.bob = U.objects.create_user("bob", password="StrongPass124!")
        cls.outsider = U.objects.create_user("outsider", password="StrongPass124!")
        for u in [cls.leader, cls.alice, cls.bob, cls.outsider]:
            Profile.objects.create(user=u)
        cat = Category.objects.create(name="Development", name_ar="التطوير")
        cls.python = Skill.objects.create(category=cat, name="Python", name_ar="بايثون")
        cls.figma = Skill.objects.create(category=cat, name="Figma", name_ar="فيجما")
        cls.team = Team.objects.create(
            owner=cls.leader,
            title="Demo team",
            category="hackathon",
            description="Build an accessible app",
            contribution="Backend development",
        )
        cls.role = Role.objects.create(
            team=cls.team, title="Designer", description="UI design", seats=1
        )
        cls.chat = Conversation.objects.create(team=cls.team)
        cls.chat.participants.add(cls.leader)
        cls.teach = TeachingSkill.objects.create(user=cls.bob, skill=cls.figma)

    def login(self, user):
        self.client.force_login(user)

    def application(self, user=None, role=None):
        return Application.objects.create(
            role=role or self.role,
            applicant=user or self.alice,
            message="I would like to help with the UI",
        )

    def accept(self, application):
        self.login(self.leader)
        return self.client.post(
            reverse("application_decide", args=[application.pk, "accept"])
        )

    def test_public_pages_and_auth_templates(self):
        for lang in ["ar", "en"]:
            self.client.cookies["django_language"] = lang
            for path in [
                "/",
                "/teams/",
                "/learn/",
                "/accounts/login/",
                "/accounts/signup/",
                f"/teams/{self.team.pk}/",
                f"/people/{self.bob.pk}/",
            ]:
                with self.subTest(lang=lang, path=path):
                    self.assertEqual(self.client.get(path).status_code, 200)

    def test_authenticated_pages(self):
        self.login(self.leader)
        for path in [
            "/accounts/profile/",
            "/teams/new/",
            "/teams/mine/",
            "/applications/",
            "/learn/skills/",
            "/learn/requests/",
            "/messages/",
            "/support/contact/",
            f"/teams/{self.team.pk}/applicants/",
            f"/messages/{self.chat.pk}/",
        ]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_protected_pages_redirect(self):
        for path in [
            "/teams/new/",
            "/accounts/profile/",
            "/applications/",
            "/messages/",
        ]:
            self.assertEqual(self.client.get(path).status_code, 302)

    def test_create_publishes_roles_and_chat_atomically(self):
        self.login(self.alice)
        data = {
            "title": "New idea",
            "category": "challenge",
            "description": "Build a new platform",
            "contribution": "I will develop it",
            "roles-TOTAL_FORMS": "1",
            "roles-INITIAL_FORMS": "0",
            "roles-MIN_NUM_FORMS": "1",
            "roles-MAX_NUM_FORMS": "12",
            "roles-0-title": "Developer",
            "roles-0-description": "Django backend",
            "roles-0-seats": "2",
            "roles-0-skills": [self.python.pk],
        }
        response = self.client.post(reverse("team_create"), data)
        self.assertEqual(response.status_code, 302)
        team = Team.objects.get(title="New idea")
        self.assertEqual(team.roles.get().seats, 2)
        self.assertTrue(
            team.conversation.participants.filter(pk=self.alice.pk).exists()
        )

    def test_missing_roles_does_not_publish(self):
        self.login(self.alice)
        response = self.client.post(
            reverse("team_create"),
            {
                "title": "Incomplete",
                "category": "challenge",
                "description": "A description",
                "contribution": "My contribution",
                "roles-TOTAL_FORMS": "0",
                "roles-INITIAL_FORMS": "0",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Team.objects.filter(title="Incomplete").exists())

    def test_apply_and_duplicate_prevention(self):
        self.login(self.alice)
        for _ in range(2):
            self.client.post(
                reverse("apply", args=[self.role.pk]),
                {"message": "I can design the app"},
            )
        self.assertEqual(Application.objects.filter(applicant=self.alice).count(), 1)

    def test_owner_cannot_apply(self):
        self.login(self.leader)
        self.assertEqual(
            self.client.post(
                reverse("apply", args=[self.role.pk]), {"message": "Hello"}
            ).status_code,
            403,
        )

    def test_accept_adds_member_and_chat(self):
        a = self.application()
        self.accept(a)
        a.refresh_from_db()
        self.assertEqual(a.status, "accepted")
        self.assertTrue(
            Membership.objects.filter(team=self.team, user=self.alice).exists()
        )
        self.assertTrue(self.chat.participants.filter(pk=self.alice.pk).exists())
        self.login(self.alice)
        self.assertContains(self.client.get(reverse("applications")), "Demo team")
        self.assertEqual(
            self.client.get(reverse("chat", args=[self.chat.pk])).status_code, 200
        )

    def test_repeated_accept_does_not_duplicate_members(self):
        a = self.application()
        self.accept(a)
        self.accept(a)
        self.assertEqual(self.team.memberships.count(), 1)

    def test_full_role_rejects_other_pending(self):
        a = self.application()
        b = self.application(self.bob)
        self.accept(a)
        b.refresh_from_db()
        self.assertEqual(b.status, "rejected")
        self.assertEqual(self.role.available, 0)
        self.accept(b)
        self.assertEqual(self.team.memberships.count(), 1)

    def test_multiple_seats_fill_without_overbooking(self):
        self.role.seats = 2
        self.role.save()
        a = self.application()
        b = self.application(self.bob)
        self.accept(a)
        b.refresh_from_db()
        self.assertEqual(b.status, "pending")
        self.accept(b)
        self.assertEqual(self.role.available, 0)
        self.assertEqual(self.team.memberships.count(), 2)

    def test_non_leader_cannot_review(self):
        a = self.application()
        self.login(self.outsider)
        self.assertEqual(
            self.client.post(
                reverse("application_decide", args=[a.pk, "accept"])
            ).status_code,
            404,
        )

    def test_close_preserves_members_and_rejects_pending(self):
        a = self.application()
        self.accept(a)
        other = Role.objects.create(
            team=self.team, title="Writer", description="Content", seats=1
        )
        b = self.application(self.bob, other)
        self.login(self.leader)
        self.client.post(reverse("close_team", args=[self.team.pk]))
        b.refresh_from_db()
        self.team.refresh_from_db()
        self.assertFalse(self.team.is_open)
        self.assertEqual(b.status, "rejected")
        self.assertEqual(self.team.memberships.count(), 1)

    def test_withdraw_only_by_applicant_and_pending(self):
        a = self.application()
        self.login(self.bob)
        self.assertEqual(
            self.client.post(reverse("withdraw", args=[a.pk])).status_code, 404
        )
        self.login(self.alice)
        self.client.post(reverse("withdraw", args=[a.pk]))
        a.refresh_from_db()
        self.assertEqual(a.status, "withdrawn")

    def test_learning_without_reciprocal_skill(self):
        self.login(self.alice)
        response = self.client.post(
            reverse("learning_create", args=[self.teach.pk]),
            {"kind": "learn", "message": "I want to learn Figma"},
        )
        self.assertEqual(response.status_code, 302)
        obj = LearningRequest.objects.get(sender=self.alice)
        self.assertIsNone(obj.offered_skill)
        self.login(self.bob)
        self.client.post(reverse("learning_decide", args=[obj.pk, "accept"]))
        self.assertEqual(obj.conversation.participants.count(), 2)

    def test_exchange_requires_own_offered_skill(self):
        other = TeachingSkill.objects.create(user=self.leader, skill=self.python)
        self.login(self.alice)
        response = self.client.post(
            reverse("learning_create", args=[self.teach.pk]),
            {
                "kind": "exchange",
                "offered_skill": other.pk,
                "message": "Teach me Figma",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(LearningRequest.objects.exists())

    def test_learning_self_request_forbidden(self):
        self.login(self.bob)
        self.assertEqual(
            self.client.get(
                reverse("learning_create", args=[self.teach.pk])
            ).status_code,
            403,
        )

    def test_request_reject_does_not_create_chat(self):
        obj = LearningRequest.objects.create(
            sender=self.alice, recipient=self.bob, teaching=self.teach, message="Hello"
        )
        self.login(self.bob)
        self.client.post(reverse("learning_decide", args=[obj.pk, "reject"]))
        self.assertFalse(Conversation.objects.filter(learning=obj).exists())

    def test_outsider_cannot_accept_learning_request(self):
        obj = LearningRequest.objects.create(
            sender=self.alice, recipient=self.bob, teaching=self.teach, message="Hello"
        )
        self.login(self.outsider)
        self.assertEqual(
            self.client.post(
                reverse("learning_decide", args=[obj.pk, "accept"])
            ).status_code,
            403,
        )

    def test_duplicate_learning_request(self):
        self.login(self.alice)
        for _ in range(2):
            self.client.post(
                reverse("learning_create", args=[self.teach.pk]),
                {"kind": "learn", "message": "I want to learn"},
            )
        self.assertEqual(LearningRequest.objects.count(), 1)

    def test_chat_access_and_idempotent_messages(self):
        self.login(self.outsider)
        for name in ["chat", "chat_messages"]:
            self.assertEqual(
                self.client.get(reverse(name, args=[self.chat.pk])).status_code, 404
            )
        self.assertEqual(
            self.client.post(
                reverse("chat_send", args=[self.chat.pk]),
                {"body": "Hello", "client_id": uuid.uuid4()},
            ).status_code,
            404,
        )
        self.login(self.leader)
        data = {"body": "<script>alert(1)</script>", "client_id": str(uuid.uuid4())}
        for _ in range(2):
            self.client.post(reverse("chat_send", args=[self.chat.pk]), data)
        self.assertEqual(self.chat.messages.count(), 1)
        response = self.client.get(reverse("chat", args=[self.chat.pk]))
        self.assertContains(response, "&lt;script&gt;")
        self.assertEqual(
            self.client.get(
                reverse("chat_messages", args=[self.chat.pk]) + "?after=bad"
            ).status_code,
            400,
        )

    def test_blank_or_long_message_rejected(self):
        self.login(self.leader)
        for text in ["   ", "x" * 2001]:
            self.assertEqual(
                self.client.post(
                    reverse("chat_send", args=[self.chat.pk]),
                    {"body": text, "client_id": uuid.uuid4()},
                ).status_code,
                400,
            )

    def test_cv_is_not_public_and_requires_consent(self):
        with TemporaryDirectory() as d, override_settings(MEDIA_ROOT=d):
            profile = self.alice.profile
            profile.resume = SimpleUploadedFile("cv.pdf", b"%PDF-1.4 test")
            profile.save()
            a = self.application()
            self.login(self.leader)
            self.assertEqual(
                self.client.get(reverse("resume", args=[self.alice.pk])).status_code,
                403,
            )
            a.share_resume = True
            a.save()
            self.assertEqual(
                self.client.get(reverse("resume", args=[self.alice.pk])).status_code,
                200,
            )
            self.login(self.outsider)
            self.assertEqual(
                self.client.get(reverse("resume", args=[self.alice.pk])).status_code,
                403,
            )
            self.assertEqual(
                self.client.get("/media/" + profile.resume.name).status_code, 404
            )

    def test_cv_validation(self):
        form = ProfileForm(
            {},
            files={"resume": SimpleUploadedFile("fake.pdf", b"not pdf")},
            instance=self.alice.profile,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("resume", form.errors)

    def test_recommendations_put_interests_first(self):
        self.alice.profile.wanted_skills.add(self.figma)
        TeachingSkill.objects.create(user=self.leader, skill=self.python)
        self.login(self.alice)
        response = self.client.get(reverse("learn"))
        self.assertEqual(list(response.context["page_obj"])[0].pk, self.bob.pk)

    def test_filter_category(self):
        response = self.client.get(reverse("explore"), {"category": "challenge"})
        self.assertEqual(response.context["page_obj"].paginator.count, 0)

    def test_private_notes_not_exposed_to_applicant(self):
        a = self.application()
        a.leader_note = "PRIVATE-LEADER-NOTE"
        a.save()
        self.login(self.alice)
        self.assertNotContains(
            self.client.get(reverse("applications")), "PRIVATE-LEADER-NOTE"
        )

    def test_csrf_and_post_only(self):
        self.login(self.leader)
        a = self.application()
        self.assertEqual(
            self.client.get(
                reverse("application_decide", args=[a.pk, "accept"])
            ).status_code,
            405,
        )
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.leader)
        self.assertEqual(
            client.post(
                reverse("application_decide", args=[a.pk, "accept"])
            ).status_code,
            403,
        )

    def test_safe_signup_redirect(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "newuser",
                "password1": "GoodStrongPass124!",
                "password2": "GoodStrongPass124!",
                "next": "https://evil.example/",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
