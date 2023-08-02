from django import forms

class FileUploadForm(forms.Form):
    file = forms.FileField(
        label='Select a CSV or JSON file',
        help_text='File must be either in CSV or JSON format.',
        widget=forms.ClearableFileInput(attrs={'accept': '.csv, .json'}),
    )
    
    database_choices = [('elasticsearch', 'Elasticsearch'), ('mongodb', 'MongoDB')]
    database = forms.ChoiceField(
        choices=database_choices,
        widget=forms.RadioSelect,
        initial='mongodb'  # Set the default value to 'mongodb'
    )

    def clean_file(self):
        file = self.cleaned_data['file']
        if file:
            file_extension = file.name.split('.')[-1].lower()
            allowed_extensions = ['csv', 'json']
            if file_extension not in allowed_extensions:
                raise forms.ValidationError('Only CSV or JSON files are allowed.')
        return file

