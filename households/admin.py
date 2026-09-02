from django.contrib import admin

from .models import (
    Chore,
    ChoreAssignment,
    Expense,
    ExpenseShare,
    Household,
    HouseholdMember,
    HouseNote,
)


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "created_by",
        "invite_code",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "name",
        "address",
        "invite_code",
        "created_by__username",
        "created_by__email",
    )
    list_filter = (
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "invite_code",
        "created_at",
        "updated_at",
    )


@admin.register(HouseholdMember)
class HouseholdMemberAdmin(admin.ModelAdmin):
    list_display = (
        "household",
        "user",
        "role",
        "joined_at",
    )
    search_fields = (
        "household__name",
        "user__username",
        "user__email",
    )
    list_filter = (
        "role",
        "joined_at",
    )
    readonly_fields = (
        "joined_at",
    )


@admin.register(Chore)
class ChoreAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "household",
        "repeat_frequency",
        "created_by",
        "active",
        "created_at",
    )
    search_fields = (
        "title",
        "description",
        "household__name",
        "created_by__username",
    )
    list_filter = (
        "repeat_frequency",
        "active",
        "created_at",
    )
    readonly_fields = (
        "created_at",
    )


@admin.register(ChoreAssignment)
class ChoreAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "chore",
        "assigned_to",
        "due_date",
        "completed",
        "completed_at",
    )
    search_fields = (
        "chore__title",
        "assigned_to__username",
        "assigned_to__email",
    )
    list_filter = (
        "completed",
        "due_date",
        "completed_at",
    )
    readonly_fields = (
        "completed_at",
    )


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "household",
        "amount",
        "paid_by",
        "date",
        "created_at",
    )
    search_fields = (
        "title",
        "notes",
        "household__name",
        "paid_by__username",
    )
    list_filter = (
        "date",
        "created_at",
    )
    readonly_fields = (
        "created_at",
    )


@admin.register(ExpenseShare)
class ExpenseShareAdmin(admin.ModelAdmin):
    list_display = (
        "expense",
        "user",
        "amount_owed",
        "settled",
        "settled_at",
    )
    search_fields = (
        "expense__title",
        "user__username",
        "user__email",
    )
    list_filter = (
        "settled",
        "settled_at",
    )
    readonly_fields = (
        "settled_at",
    )


@admin.register(HouseNote)
class HouseNoteAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "household",
        "created_by",
        "created_at",
    )
    search_fields = (
        "title",
        "body",
        "household__name",
        "created_by__username",
    )
    list_filter = (
        "created_at",
    )
    readonly_fields = (
        "created_at",
    )