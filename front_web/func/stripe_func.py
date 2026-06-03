import stripe
from django.conf import settings
from decimal import Decimal, ROUND_HALF_UP
from courses.models import Course, SignUp
from students.models import Student
from datetime import datetime
from django.utils import timezone
from django.db import transaction

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION

def _money_to_stripe_amount(amount):
    return int((Decimal(amount) * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _stripe_value_id(value):
    if not value:
        return ""
    if isinstance(value, str):
        return value
    return value.get("id", "")


def _stripe_object_value(obj, key, default=None):
    if hasattr(obj, "get"):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _create_signup_from_checkout_session(session):
    
    metadata = _stripe_object_value(session, "metadata", {}) or {}

    course_id = _stripe_object_value(metadata, "course_id")
    student_id = _stripe_object_value(metadata, "student_id")
    session_id = _stripe_object_value(session, "id")

    if not course_id or not student_id or not session_id:
        raise ValueError("Stripe Checkout Session is missing course_id or student_id metadata.")

    with transaction.atomic():
        course = Course.objects.select_for_update().get(id=course_id)
        student = Student.objects.get(id=student_id)

        existing_signup = SignUp.objects.filter(online_payment_session=session_id).first()
        if existing_signup:
            return existing_signup, False

        existing_paid_signup = SignUp.objects.filter(
            course=course,
            student=student,
            is_reject=False,
        ).exclude(payment_ref="").first()
        if existing_paid_signup:
            return existing_paid_signup, False

        current_datetime = timezone.localtime(timezone.now())
        payment_method = ""
        payment_method_types = _stripe_object_value(session, "payment_method_types", []) or []
        if payment_method_types:
            payment_method = payment_method_types[0]

        payment_intent = _stripe_value_id(_stripe_object_value(session, "payment_intent"))
        amount_total = _stripe_object_value(session, "amount_total", 0) or 0
        created_timestamp = _stripe_object_value(session, "created")
        payment_date = current_datetime
        if created_timestamp:
            payment_date = datetime.fromtimestamp(created_timestamp, tz=timezone.get_current_timezone())

        signup = SignUp.objects.create(
            student=student,
            course=course,
            status="signup success",
            sign_up_date=current_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            payment_date=payment_date,
            payment_amount=Decimal(amount_total) / Decimal("100"),
            payment_method=payment_method or "Stripe",
            payment_ref=payment_intent or session_id,
            online_payment_intent=payment_intent,
            online_payment_session=session_id,
            payment_remarks="",
            file_status="created",
            created_by=f"student_id:{student.id}",
            created_datetime=current_datetime,
            last_updated_by=f"student_id:{student.id}",
            last_updated_datetime=current_datetime,
        )
        return signup, True