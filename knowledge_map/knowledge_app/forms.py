from django import forms
from .models import Quiz, UploadedFile
 
 
class QuizGenerationForm(forms.ModelForm):
    """Form for generating new quizzes from existing PDFs, uploads, or text"""
    
    source_choice = forms.ChoiceField(
        choices=[
            ('existing', 'Select Existing PDF'),
            ('upload', 'Upload New PDF'),
            ('text', 'Paste Text')
        ],
        initial='pdf',
        widget=forms.RadioSelect,
        label='Quiz Source'
    )
    
    # Select from existing uploaded files
    existing_pdf = forms.ModelChoiceField(
        queryset=UploadedFile.objects.none(),
        required=False,
        label='Select a PDF from your uploads',
    )
    
    # Upload new PDF
    pdf_file = forms.FileField(
        required=False,
        label='Upload New PDF File',
        widget=forms.FileInput(attrs={'accept': '.pdf'})
    )
    
    # Or paste text
    text_input = forms.CharField(
        required=False,
        label='Paste Text Content',
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': 'Paste the text you want to create a quiz from...'
        })
    )
    
    num_questions = forms.IntegerField(
        initial=5,
        min_value=1,
        max_value=50,
        label='Number of Questions'
    )
    
    question_types = forms.MultipleChoiceField(
        choices=[
            ('multiple_choice', 'Multiple Choice'),
            ('fill_in_blank', 'Fill in the Blank'),
            ('true_false', 'True/False'),
            ('matching', 'Matching'),
            ('short_answer', 'Short Answer'),
        ],
        widget=forms.CheckboxSelectMultiple,
        label='Question Types to Include'
    )
    
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'difficulty']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g., Biology Chapter 3 Quiz',
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Optional description...',
            }),
            'difficulty': forms.Select(),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to only user's uploaded files
        if user:
            self.fields['existing_pdf'].queryset = UploadedFile.objects.filter(user=user)
    
    def clean(self):
        cleaned_data = super().clean()
        source_choice = cleaned_data.get('source_choice')
        existing_pdf = cleaned_data.get('existing_pdf')
        pdf_file = cleaned_data.get('pdf_file')
        text_input = cleaned_data.get('text_input')
        
        # Validate based on source choice
        if source_choice == 'existing' and not existing_pdf:
            self.add_error('existing_pdf', 'Please select a PDF file')
        elif source_choice == 'upload' and not pdf_file:
            self.add_error('pdf_file', 'Please upload a PDF file')
        elif source_choice == 'text' and not text_input:
            self.add_error('text_input', 'Please paste text content')
        
        return cleaned_data
 