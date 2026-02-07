from django import forms
from django.contrib.auth import get_user_model
from .models import DeveloperProfile, Team, Project, Task, CodeReview

User = get_user_model()

# Existing forms (reconstructed based on views.py imports and usage)

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'description']

class TeamMemberForm(forms.Form):
    email = forms.EmailField(label="Member Email")
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('contributor', 'Contributor'),
        ('reviewer', 'Reviewer'),
        ('leader', 'Leader'),
        ('admin', 'Admin'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES)

class ProjectForm(forms.ModelForm):
    team = forms.ModelChoiceField(queryset=Team.objects.none())
    tags = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = Project
        fields = ['team', 'name', 'description', 'status', 'project_type', 'tags']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Limit team queryset to teams the user is a member of
            self.fields['team'].queryset = user.teams.all()


class TeamCreateForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'description']


class TeamInviteForm(forms.Form):
    emails = forms.CharField(widget=forms.Textarea, label="Email Addresses (comma-separated)")

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['project', 'title', 'description', 'assigned_to', 'status', 'priority', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4})
        }

class CodeReviewForm(forms.ModelForm):
    project = forms.ModelChoiceField(queryset=Project.objects.none())
    reviewer = forms.ModelChoiceField(queryset=User.objects.none(), required=False)

    class Meta:
        model = CodeReview
        fields = ['project', 'title', 'reviewer']
        widgets = {
             # 'code_snippet': forms.Textarea(attrs={'rows': 10}) # Removed widget as field is removed
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
             # Limit project queryset to projects the user can view
             self.fields['project'].queryset = Project.objects.filter(team__members=user).distinct()
            # Limit reviewer queryset - This might need refinement based on selected project
             self.fields['reviewer'].queryset = User.objects.filter(teammember__team__projects__in=self.fields['project'].queryset).distinct()

    # def clean_code_snippet(self):
    #     url = self.cleaned_data['code_snippet']
    #     if 'github.com' in url and '/pull/' in url:
    #         pass
    #     elif not url.strip():
    #          raise forms.ValidationError('Code snippet or GitHub PR URL is required.')
    #     return url

# Profile Edit Form
class ProfileEditForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()

    class Meta:
        model = DeveloperProfile
        fields = ['bio', 'github_username']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['username'].initial = user.username
            self.fields['email'].initial = user.email

    def save(self, commit=True):
        profile = super().save(commit=commit)
        user = profile.user
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return profile

# Settings Form
class SettingsForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    username = forms.CharField(max_length=150)
    email = forms.EmailField()

    class Meta:
        model = DeveloperProfile
        fields = [] # Remove fields that don't exist on the model

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['username'].initial = user.username
            self.fields['email'].initial = user.email

    def save(self, commit=True):
        profile = super().save(commit=commit)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return profile 