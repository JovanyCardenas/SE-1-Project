from django.db import models
import secrets, string
from django.conf import settings
from django.utils import timezone

USER = settings.AUTH_USER_MODEL

def generate_invite_code():
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))

class Household(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100, blank=True)
    invite_code = models.CharField(max_length=20, unique=True, default=generate_invite_code)
    created_by = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="created_households")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class HouseholdMember(models.Model):
    MEMBER_ROLES = [
        ("owner", "Owner"),
        ("member", "Member"),
    ]

    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="household_memberships")
    role = models.CharField(choices=MEMBER_ROLES, max_length=20, default="member")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("household", "user")

    def __str__(self):
        return f"{self.user.username} - {self.household.name}"

class Chore(models.Model):
    REPEAT_CHOICES = [
        ("none", "Does not repeat"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("biweekly", "Every 2 Weeks"),
        ("monthly", "Monthly"),
        ("bimonthly", "Every Other Month"),
        ("quarterly", "Quarterly"),
    ]
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="chores")
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    repeat_frequency = models.CharField(choices=REPEAT_CHOICES, max_length=20, default="none")
    created_by = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="created_chores")
    active = models.BooleanField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ChoreAssignment(models.Model):
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE, related_name="assignments")
    assigned_to = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="chore_assignments")
    due_date = models.DateTimeField()
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    def mark_complete(self):
        self.completed = True
        self.completed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.chore.title} assigned to {self.assigned_to.username}"

class Expense(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="expenses")
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    paid_by = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="paid_expenses")
    date = models.DateTimeField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - ${self.amount}"

class ExpenseShare(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="shares")
    user = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="expense_shares")
    amount_owed = models.DecimalField(max_digits=8, decimal_places=2)
    settled = models.BooleanField(default=False)
    settled_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("expense", "user")

    def mark_settled(self):
        self.settled = True
        self.settled_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.user.username} owes ${self.amount_owed}"

class HouseNote(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="notes")
    title = models.CharField(max_length=100)
    body = models.TextField(blank=True)
    created_by = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="house_notes")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title