from django.shortcuts import render, redirect, get_object_or_404
from .form import FileUploadForm
from .models import UploadedFile

def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            database_choice = form.cleaned_data['database']  # Get the selected database choice
            print(database_choice)
            instance = UploadedFile(file=uploaded_file)
            instance.save()
            # Process the selected database choice here, e.g., send it to template or perform specific actions
            return redirect('upload_success')
    else:
        form = FileUploadForm()
    return render(request, 'fileuploader/upload.html', {'form': form})

def upload_success(request):
    return render(request, 'fileuploader/upload_success.html')

def file_list(request):
    files = UploadedFile.objects.all()
    return render(request, 'fileuploader/file_list.html', {'files': files})

def file_detail(request, pk):
    file = get_object_or_404(UploadedFile, pk=pk)
    return render(request, 'fileuploader/file_detail.html', {'file': file})

def file_update(request, pk):
    file = get_object_or_404(UploadedFile, pk=pk)
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file.file = form.cleaned_data['file']
            file.database = form.cleaned_data['database']
            file.save()
            return redirect('file_list')
    else:
        form = FileUploadForm(initial={'file': file.file, 'database': file.database})
    return render(request, 'fileuploader/file_update.html', {'form': form, 'file': file})

def file_delete(request, pk):
    file = get_object_or_404(UploadedFile, pk=pk)
    if request.method == 'POST':
        file.delete()
        return redirect('file_list')
    return render(request, 'fileuploader/file_delete.html', {'file': file})

