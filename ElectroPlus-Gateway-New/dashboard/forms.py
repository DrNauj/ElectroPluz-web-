from django import forms

class PeriodForm(forms.Form):
    period = forms.ChoiceField(
        choices=[
            ('today', 'Hoy'),
            ('week', 'Esta semana'),
            ('month', 'Este mes'),
            ('year', 'Este año'),
        ],
        required=False,
        initial='month',
        label='Período'
    )
