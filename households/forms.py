from django import forms

from .models import *


class HouseholdForm(forms.ModelForm):
    class Meta:
        model = Household
        fields = [
            "name",
            "address",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Apartment 204, Spartan House, etc.",
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "placeholder": "Optional address or location nickname",
                }
            ),
        }


class JoinHouseholdForm(forms.Form):
    invite_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter invite code",
            }
        ),
    )

    def clean_invite_code(self):
        invite_code = self.cleaned_data["invite_code"].strip().upper()
        return invite_code


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            "title",
            "amount",
            "date",
            "notes",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Laundry detergent, toilet paper, groceries, etc.",
                }
            ),
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Optional notes about this expense",
                }
            ),
        }


class ChoreForm(forms.ModelForm):
    class Meta:
        model = Chore
        fields = [
            "title",
            "description",
            "repeat_frequency",
            "active",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Take out trash, clean kitchen, vacuum, etc.",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Optional details about this chore",
                }
            ),
        }


class ChoreAssignmentForm(forms.ModelForm):
    class Meta:
        model = ChoreAssignment
        fields = [
            "assigned_to",
            "due_date",
        ]
        widgets = {
            "due_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
        }