from django.shortcuts import render, redirect, get_object_or_404
from .forms import GradeBookComponentsForm
from .models import GradeBookComponents
# Create your views here.

#View GradeBookComponents
def viewGradeBookComponents(request):
    gradebookcomponents = GradeBookComponents.objects.all()
    return render(request, 'gradebookcomponent/gradeBook.html', {'gradebookcomponents': gradebookcomponents})


#Create GradeBookComponents
def createGradeBookComponents(request):
    if request.method == 'POST':
        form = GradeBookComponentsForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('courseList')
    else:
        form = GradeBookComponentsForm()
    
    return render(request, 'gradebookcomponent/createGradeBook.html', {'form': form})

#Modify GradeBookComponents
def updateGradeBookComponents(request, pk):
    gradebookcomponent = get_object_or_404(GradeBookComponents, pk=pk)
    if request.method == 'POST':
        form = GradeBookComponentsForm(request.POST, instance=gradebookcomponent)
        if form.is_valid():
            form.save()
            return redirect('courseList')
    else:
        form = GradeBookComponentsForm(instance=gradebookcomponent)
    
    return render(request, 'gradebookcomponent/updateGradeBook.html', {'form': form})

#Delete GradeBookComponents
def deleteGradeBookComponents(request, pk):
    gradebookcomponent = get_object_or_404(GradeBookComponents, pk=pk)
    gradebookcomponent.delete()
    return redirect('viewGradeBookComponents')

#View GradeBookComponents
def viewGradeBookComponents(request):
    gradebookcomponents = GradeBookComponents.objects.all()
    return render(request, 'gradebookcomponent/viewGradeBook.html', {'gradebookcomponents': gradebookcomponents})



