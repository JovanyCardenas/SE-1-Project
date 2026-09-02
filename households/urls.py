from django.urls import path

from .views import *

urlpatterns = [
    path("", household_list, name="household_list"),
    path("create/", create_household, name="create_household"),
    path("join/", join_household, name="join_household"),
    path("<int:household_id>/", household_detail, name="household_detail"),
    path("<int:household_id>/expenses/create/", create_expense, name="create_expense"),
    path("<int:household_id>/chores/create/", create_chore, name="create_chore"),
    path("<int:household_id>/notes/create/", create_note, name="create_note"),
    path("expenses/shares/<int:share_id>/settle/", settle_expense_share, name="settle_expense_share"),
    path("chores/<int:chore_id>/assign/", assign_chore, name="assign_chore"),
    path("chores/<int:chore_id>/assign-random/", assign_chore_randomly, name="assign_chore_randomly"),
    path("chores/assignments/<int:assignment_id>/complete/", complete_chore_assignment, name="complete_chore_assignment"),
    
    path("<int:household_id>/members/", manage_members, name="manage_household_members"),
    path("<int:household_id>/members/<int:member_id>/remove/", remove_member, name="remove_household_member"),
    path("<int:household_id>/members/<int:member_id>/transfer-ownership/", transfer_ownership, name="transfer_household_ownership"),
    path("<int:household_id>/invite/regenerate/", regenerate_invite_code, name="regenerate_invite_code"),

    path("expenses/<int:expense_id>/edit/", edit_expense, name="edit_expense"),
    path("expenses/<int:expense_id>/delete/", delete_expense, name="delete_expense"),

    path("chores/<int:chore_id>/edit/", edit_chore, name="edit_chore"),
    path("chores/<int:chore_id>/delete/", delete_chore, name="delete_chore"),
]