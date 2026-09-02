import random
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from core.decorators import feature_required

from .forms import *
from .models import *


def user_is_household_member(user, household):
    return HouseholdMember.objects.filter(
        household=household,
        user=user,
    ).exists()


def user_is_household_owner(user, household):
    return HouseholdMember.objects.filter(
        household=household,
        user=user,
        role="owner",
    ).exists()


def get_household_for_member(household_id, user):
    household = get_object_or_404(Household, id=household_id)

    if not user_is_household_member(user, household):
        raise PermissionDenied

    return household


@feature_required("households")
@login_required
def household_list(request):
    memberships = (
        HouseholdMember.objects
        .filter(user=request.user)
        .select_related("household")
        .order_by("household__name")
    )

    return render(
        request,
        "households/household_list.html",
        {
            "memberships": memberships,
        },
    )

@feature_required("households")
@login_required
def create_household(request):
    if request.method == "POST":
        form = HouseholdForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                household = form.save(commit=False)
                household.created_by = request.user
                household.save()

                HouseholdMember.objects.create(
                    household=household,
                    user=request.user,
                    role="owner",
                )

            messages.success(request, "Household created successfully.")
            return redirect("household_detail", household_id=household.id)
    else:
        form = HouseholdForm()

    return render(
        request,
        "households/create_household.html",
        {
            "form": form,
        },
    )

@feature_required("households")
@login_required
def join_household(request):
    if request.method == "POST":
        form = JoinHouseholdForm(request.POST)

        if form.is_valid():
            invite_code = form.cleaned_data["invite_code"].strip().upper()
            household = get_object_or_404(Household, invite_code=invite_code)

            membership, created = HouseholdMember.objects.get_or_create(
                household=household,
                user=request.user,
                defaults={"role": "member"},
            )

            if created:
                messages.success(request, f"You joined {household.name}.")
            else:
                messages.info(request, f"You are already a member of {household.name}.")

            return redirect("household_detail", household_id=household.id)
    else:
        form = JoinHouseholdForm()

    return render(
        request,
        "households/join_household.html",
        {
            "form": form,
        },
    )


@login_required
def household_detail(request, household_id):
    household = get_household_for_member(household_id, request.user)

    members = (
        HouseholdMember.objects
        .filter(household=household)
        .select_related("user")
        .order_by("role", "user__username")
    )

    chores = (
        Chore.objects
        .filter(household=household, active=True)
        .select_related("created_by")
        .order_by("title")
    )

    my_chore_assignments = (
        ChoreAssignment.objects
        .filter(chore__household=household, assigned_to=request.user)
        .select_related("chore")
        .order_by("completed", "due_date")
    )

    recent_chore_assignments = (
        ChoreAssignment.objects
        .filter(chore__household=household)
        .select_related("chore", "assigned_to")
        .order_by("completed", "due_date")[:10]
    )

    expenses = (
        Expense.objects
        .filter(household=household)
        .select_related("paid_by")
        .prefetch_related("shares")
        .order_by("-date", "-created_at")[:10]
    )

    my_expense_shares = (
        ExpenseShare.objects
        .filter(expense__household=household, user=request.user, settled=False)
        .select_related("expense")
        .order_by("expense__date")
    )

    notes = (
        HouseNote.objects
        .filter(household=household)
        .select_related("created_by")
        .order_by("-created_at")[:5]
    )

    return render(
        request,
        "households/household_detail.html",
        {
            "household": household,
            "members": members,
            "chores": chores,
            "my_chore_assignments": my_chore_assignments,
            "recent_chore_assignments": recent_chore_assignments,
            "expenses": expenses,
            "my_expense_shares": my_expense_shares,
            "notes": notes,
            "is_owner": user_is_household_owner(request.user, household),
        },
    )


@login_required
def create_expense(request, household_id):
    household = get_household_for_member(household_id, request.user)
    members = HouseholdMember.objects.filter(household=household).select_related("user")

    if request.method == "POST":
        form = ExpenseForm(request.POST)
        selected_user_ids = request.POST.getlist("split_between")

        if form.is_valid():
            if not selected_user_ids:
                messages.error(request, "Select at least one person to split the expense with.")
            else:
                with transaction.atomic():
                    expense = form.save(commit=False)
                    expense.household = household
                    expense.paid_by = request.user
                    expense.save()

                    split_amount = expense.amount / Decimal(len(selected_user_ids))

                    for user_id in selected_user_ids:
                        if members.filter(user_id=user_id).exists():
                            ExpenseShare.objects.create(
                                expense=expense,
                                user_id=user_id,
                                amount_owed=split_amount,
                            )

                messages.success(request, "Expense created and split successfully.")
                return redirect("household_detail", household_id=household.id)
    else:
        form = ExpenseForm()

    return render(
        request,
        "households/create_expense.html",
        {
            "form": form,
            "household": household,
            "members": members,
        },
    )


@login_required
def settle_expense_share(request, share_id):
    share = get_object_or_404(
        ExpenseShare.objects.select_related("expense", "expense__household"),
        id=share_id,
        user=request.user,
    )

    if request.method == "POST":
        share.settled = True
        share.settled_at = timezone.now()
        share.save()

        messages.success(request, "Expense share marked as settled.")

    return redirect("household_detail", household_id=share.expense.household.id)


@login_required
def create_chore(request, household_id):
    household = get_household_for_member(household_id, request.user)

    if request.method == "POST":
        form = ChoreForm(request.POST)

        if form.is_valid():
            chore = form.save(commit=False)
            chore.household = household
            chore.created_by = request.user
            chore.save()

            messages.success(request, "Chore created successfully.")
            return redirect("household_detail", household_id=household.id)
    else:
        form = ChoreForm()

    return render(
        request,
        "households/create_chore.html",
        {
            "form": form,
            "household": household,
        },
    )


@login_required
def assign_chore(request, chore_id):
    chore = get_object_or_404(Chore, id=chore_id)
    household = chore.household

    if not user_is_household_member(request.user, household):
        raise PermissionDenied

    members = HouseholdMember.objects.filter(household=household).select_related("user")

    if request.method == "POST":
        form = ChoreAssignmentForm(request.POST)

        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.chore = chore

            selected_user = assignment.assigned_to

            if not members.filter(user=selected_user).exists():
                messages.error(request, "That user is not a member of this household.")
            else:
                assignment.save()
                messages.success(request, "Chore assigned successfully.")
                return redirect("household_detail", household_id=household.id)
    else:
        form = ChoreAssignmentForm()

    return render(
        request,
        "households/assign_chore.html",
        {
            "form": form,
            "chore": chore,
            "household": household,
            "members": members,
        },
    )


@login_required
def assign_chore_randomly(request, chore_id):
    chore = get_object_or_404(Chore, id=chore_id)
    household = chore.household

    if not user_is_household_member(request.user, household):
        raise PermissionDenied

    members = list(
        HouseholdMember.objects
        .filter(household=household)
        .select_related("user")
    )

    if not members:
        messages.error(request, "There are no household members to assign this chore to.")
        return redirect("household_detail", household_id=household.id)

    selected_member = random.choice(members)

    ChoreAssignment.objects.create(
        chore=chore,
        assigned_to=selected_member.user,
        due_date=timezone.now().date(),
    )

    messages.success(
        request,
        f"{chore.title} was assigned to {selected_member.user.username}.",
    )

    return redirect("household_detail", household_id=household.id)


@login_required
def complete_chore_assignment(request, assignment_id):
    assignment = get_object_or_404(
        ChoreAssignment.objects.select_related("chore", "chore__household"),
        id=assignment_id,
    )

    household = assignment.chore.household

    if assignment.assigned_to != request.user and not user_is_household_owner(request.user, household):
        raise PermissionDenied

    if request.method == "POST":
        assignment.completed = True
        assignment.completed_at = timezone.now()
        assignment.save()

        messages.success(request, "Chore marked as complete.")

    return redirect("household_detail", household_id=household.id)


@login_required
def create_note(request, household_id):
    household = get_household_for_member(household_id, request.user)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        body = request.POST.get("body", "").strip()

        if title:
            HouseNote.objects.create(
                household=household,
                title=title,
                body=body,
                created_by=request.user,
            )
            messages.success(request, "Note added successfully.")
        else:
            messages.error(request, "Note title is required.")

    return redirect("household_detail", household_id=household.id)

@login_required
def manage_members(request, household_id):
    household = get_household_for_member(household_id, request.user)

    if not user_is_household_owner(request.user, household):
        raise PermissionDenied

    members = HouseholdMember.objects.filter(household=household).select_related("user")

    return render(
        request,
        "households/manage_members.html",
        {
            "household": household,
            "members": members,
        },
    )

@login_required
def remove_member(request, household_id, member_id):
    household = get_household_for_member(household_id, request.user)

    if not user_is_household_owner(request.user, household):
        raise PermissionDenied

    member = get_object_or_404(HouseholdMember, id=member_id, household=household)

    if member.user == request.user:
        messages.error(request, "You cannot remove yourself as the owner.")
        return redirect("manage_household_members", household_id=household.id)

    if request.method == "POST":
        member.delete()
        messages.success(request, "Member removed from household.")

    return redirect("manage_household_members", household_id=household.id)

@login_required
def transfer_ownership(request, household_id, member_id):
    household = get_household_for_member(household_id, request.user)

    if not user_is_household_owner(request.user, household):
        raise PermissionDenied

    new_owner = get_object_or_404(
        HouseholdMember,
        id=member_id,
        household=household,
    )

    if new_owner.user == request.user:
        messages.info(request, "You are already the owner.")
        return redirect("manage_household_members", household_id=household.id)

    if request.method == "POST":
        confirmation = request.POST.get("confirmation", "").strip()

        if confirmation != household.name:
            messages.error(request, "Ownership transfer confirmation did not match.")
            return redirect("manage_household_members", household_id=household.id)

        with transaction.atomic():
            HouseholdMember.objects.filter(
                household=household,
                role="owner",
            ).update(role="member")

            new_owner.role = "owner"
            new_owner.save()

            household.created_by = new_owner.user
            household.save()

        messages.success(request, f"Ownership transferred to {new_owner.user.username}.")

    return redirect("manage_household_members", household_id=household.id)

@login_required
def regenerate_invite_code(request, household_id):
    household = get_household_for_member(household_id, request.user)

    if not user_is_household_owner(request.user, household):
        raise PermissionDenied

    if request.method == "POST":
        household.invite_code = generate_invite_code()
        household.save()
        messages.success(request, "Invite code regenerated.")

    return redirect("manage_household_members", household_id=household.id)

@login_required
def edit_chore(request, chore_id):
    chore = get_object_or_404(Chore, id=chore_id)
    household = chore.household

    if not user_is_household_owner(request.user, household):
        raise PermissionDenied

    if request.method == "POST":
        form = ChoreForm(request.POST, instance=chore)

        if form.is_valid():
            form.save()
            messages.success(request, "Chore updated successfully.")
            return redirect("household_detail", household_id=household.id)
    else:
        form = ChoreForm(instance=chore)

    return render(
        request,
        "households/edit_chore.html",
        {
            "form": form,
            "chore": chore,
            "household": household,
        },
    )

@login_required
def delete_chore(request, chore_id):
    chore = get_object_or_404(Chore, id=chore_id)
    household = chore.household

    if not user_is_household_owner(request.user, household):
        raise PermissionDenied

    if request.method == "POST":
        chore.delete()
        messages.success(request, "Chore deleted successfully.")
        return redirect("household_detail", household_id=household.id)

    return render(
        request,
        "households/confirm_delete.html",
        {
            "object_name": chore.title,
            "cancel_url": "household_detail",
            "cancel_id": household.id,
        },
    )

@login_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(
        Expense.objects.select_related("household", "paid_by"),
        id=expense_id,
    )
    household = expense.household

    if not user_is_household_owner(request.user, household):
        raise PermissionDenied

    members = HouseholdMember.objects.filter(household=household).select_related("user")

    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)
        selected_user_ids = request.POST.getlist("split_between")

        if form.is_valid():
            if not selected_user_ids:
                messages.error(request, "Select at least one person to split the expense with.")
            else:
                with transaction.atomic():
                    expense = form.save()

                    ExpenseShare.objects.filter(expense=expense).delete()

                    split_amount = expense.amount / Decimal(len(selected_user_ids))

                    for user_id in selected_user_ids:
                        if members.filter(user_id=user_id).exists():
                            ExpenseShare.objects.create(
                                expense=expense,
                                user_id=user_id,
                                amount_owed=split_amount,
                            )

                messages.success(request, "Expense updated successfully.")
                return redirect("household_detail", household_id=household.id)
    else:
        form = ExpenseForm(instance=expense)

    selected_share_user_ids = ExpenseShare.objects.filter(
        expense=expense,
    ).values_list("user_id", flat=True)

    return render(
        request,
        "households/edit_expense.html",
        {
            "form": form,
            "expense": expense,
            "household": household,
            "members": members,
            "selected_share_user_ids": selected_share_user_ids,
        },
    )

@login_required
def delete_expense(request, expense_id):
    expense = get_object_or_404(
        Expense.objects.select_related("household"),
        id=expense_id,
    )
    household = expense.household

    if not user_is_household_owner(request.user, household):
        raise PermissionDenied

    if request.method == "POST":
        expense.delete()
        messages.success(request, "Expense deleted successfully.")
        return redirect("household_detail", household_id=household.id)

    return render(
        request,
        "households/confirm_delete.html",
        {
            "object_name": expense.title,
            "object_type": "expense",
            "cancel_url": "household_detail",
            "cancel_id": household.id,
        },
    )