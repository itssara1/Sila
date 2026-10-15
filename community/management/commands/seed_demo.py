from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from accounts.models import Profile
from skills.models import Category, Skill
from community.models import Team, Role, TeachingSkill, Conversation


class Command(BaseCommand):
    help = "Create fictitious local demo accounts and example teams. Never run on a public production database."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        categories = {
            "Development": (
                "التطوير",
                [
                    ("Python", "بايثون"),
                    ("Django", "جانغو"),
                    ("JavaScript", "جافاسكربت"),
                    ("React", "ريأكت"),
                ],
            ),
            "Design": (
                "التصميم",
                [("Figma", "فيجما"), ("UI/UX", "تصميم تجربة المستخدم")],
            ),
            "Data & AI": (
                "البيانات والذكاء الاصطناعي",
                [
                    ("Data Analysis", "تحليل البيانات"),
                    ("Machine Learning", "تعلّم الآلة"),
                ],
            ),
            "Business & Content": (
                "الأعمال والمحتوى",
                [
                    ("Project Management", "إدارة المشاريع"),
                    ("Writing", "الكتابة"),
                    ("Marketing", "التسويق"),
                ],
            ),
        }
        skills = {}
        for en, (ar, rows) in categories.items():
            category, _ = Category.objects.get_or_create(
                name=en, defaults={"name_ar": ar}
            )
            for name, name_ar in rows:
                skills[name], _ = Skill.objects.get_or_create(
                    name=name, defaults={"category": category, "name_ar": name_ar}
                )
        users = {}
        for username, name, bio in [
            ("demo_sara", "سارة", "مطوّرة ويب، أحب بناء أفكار مفيدة وتعلّم التصميم."),
            ("demo_noura", "نورة", "مصممة واجهات، أحب مشاركة خبرتي في فيجما."),
            ("demo_ali", "علي", "مهتم بتحليل البيانات والذكاء الاصطناعي."),
        ]:
            user, created = get_user_model().objects.get_or_create(
                username=username, defaults={"first_name": name}
            )
            if created:
                user.set_password("SilaDemo123!")
                user.save()
            profile, _ = Profile.objects.get_or_create(user=user, defaults={"bio": bio})
            users[username] = user
        for username, teach, wanted in [
            ("demo_sara", "Python", "Figma"),
            ("demo_noura", "Figma", "Python"),
            ("demo_ali", "Data Analysis", "Django"),
        ]:
            TeachingSkill.objects.get_or_create(
                user=users[username],
                skill=skills[teach],
                defaults={"level": "advanced"},
            )
            users[username].profile.wanted_skills.add(skills[wanted])
        for title, category, desc, role, skill in [
            (
                "أثر — إعادة تدوير أذكى",
                "hackathon",
                "نبني حلًا يساعد الزوار على فرز المخلفات وإحداث أثر بيئي إيجابي. نبحث عن رفاق يشاركوننا الفكرة.",
                "مصمم UI/UX",
                "Figma",
            ),
            (
                "لوحة بيانات تصنع الفرق",
                "challenge",
                "نكوّن فريقًا لتحليل البيانات وتحويلها إلى رؤى واضحة تساعد على اتخاذ القرار.",
                "محلل بيانات",
                "Data Analysis",
            ),
            (
                "واجهة لمشروع ناشئ",
                "freelance",
                "نتعاون لتصميم وبناء موقع تعريفي لمشروع ناشئ، بهدف التعلّم وإثراء معرض الأعمال. بدون مقابل مادي.",
                "مطور واجهة أمامية",
                "React",
            ),
        ]:
            team, _ = Team.objects.get_or_create(
                owner=users["demo_sara"],
                title=title,
                defaults={
                    "category": category,
                    "description": desc,
                    "contribution": "سأتولى تطوير الواجهة الخلفية وربطها بالتصميم.",
                },
            )
            r, _ = Role.objects.get_or_create(
                team=team,
                title=role,
                defaults={
                    "description": "نبحث عن شخص متحمس للتعاون ومشاركة خبرته.",
                    "seats": 2,
                },
            )
            r.skills.add(skills[skill])
            chat, _ = Conversation.objects.get_or_create(team=team)
            chat.participants.add(team.owner)
        self.stdout.write(
            self.style.SUCCESS(
                "Demo ready: demo_sara, demo_noura, demo_ali / SilaDemo123!"
            )
        )
