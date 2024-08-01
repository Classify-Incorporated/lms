from django.shortcuts import render, redirect
from .forms import roleForm
from .models import Role
from django.shortcuts import get_object_or_404

#Role List
def roleList(request):
    roles = Role.objects.all()
    return render(request, 'role/role.html',{'roles': roles})

# Create your views here.
def createRole(request):
    if request.method == 'POST':
        form = roleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('roleList')
    else:
        form = roleForm()
    return render(request, 'role/add_role.html', {'form': form})

def updateRole(request, pk):
    role = get_object_or_404(Role, pk=pk)
    if request.method == 'POST':
        form = roleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = roleForm(instance=role)
    
    return render(request, 'edit_role.html', {'form': form})

def deleteRole(request, pk):
    role = get_object_or_404(Role, pk=pk)
    role.delete()
    return redirect('success')
