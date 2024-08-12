from django.shortcuts import render, redirect
from .forms import roleForm
from .models import Role
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import Permission
from collections import defaultdict

#Role List
def roleList(request):
    form = roleForm()
    roles = Role.objects.all()
    permissions = Permission.objects.filter(content_type__app_label__in=['course', 'activity', 'module', 'message', 'gradebookcomponent', 'studentgrade'])

    structured_permissions = defaultdict(lambda: {'add': None, 'view': None, 'change': None, 'delete': None})
    for perm in permissions:
        action = perm.codename.split('_')[0]
        model = perm.content_type.model
        if action in ['add', 'view', 'change', 'delete']:
            structured_permissions[model][action] = perm

    return render(request, 'role/roleList.html', {'roles': roles, 'structured_permissions': dict(structured_permissions), 'form': form})

def viewRole(request, role_id):
    role_obj = get_object_or_404(Role, id=role_id)
    
    permissions = Permission.objects.filter(content_type__app_label__in=['course', 'activity', 'module', 'message', 'gradebookcomponent', 'studentgrade'])
    
    structured_permissions = defaultdict(lambda: {'add': None, 'view': None, 'change': None, 'delete': None})
    for perm in permissions:
        action = perm.codename.split('_')[0]
        model = perm.content_type.model
        if action in ['add', 'view', 'change', 'delete']:
            structured_permissions[model][action] = perm
    
    return render(request, 'role/viewRole.html', {
        'role': role_obj,
        'structured_permissions': dict(structured_permissions),
    })

# Create your views here.
def createRole(request):
    if request.method == 'POST':
        form = roleForm(request.POST)
        if form.is_valid():
            role = form.save() 

            selected_permissions = request.POST.getlist('permissions')
            permissions = Permission.objects.filter(id__in=selected_permissions)
            
            role.permissions.set(permissions)
            
            return redirect('display_role')
    else:
        form = roleForm()

    permissions = Permission.objects.filter(content_type__app_label__in=['accounts','subject','course', 'activity', 'module', 'message', 'gradebookcomponent', 'studentgrade','roles'])

    structured_permissions = defaultdict(lambda: {'add': None, 'view': None, 'change': None, 'delete': None})
    for perm in permissions:
        action = perm.codename.split('_')[0]
        model = perm.content_type.model
        if action in ['add', 'view', 'change', 'delete']:
            structured_permissions[model][action] = perm

    return render(request, 'role/addRole.html', {
        'form': form,
        'structured_permissions': dict(structured_permissions),
    })


def updateRole(request, pk):
    role_obj = get_object_or_404(Role, pk=pk)
    
    permissions = Permission.objects.filter(content_type__app_label__in=['accounts','subject','course', 'activity', 'module', 'message', 'gradebookcomponent', 'studentgrade','roles'])
    
    structured_permissions = defaultdict(lambda: {'add': None, 'view': None, 'change': None, 'delete': None})
    for perm in permissions:
        action = perm.codename.split('_')[0]
        model = perm.content_type.model
        if action in ['add', 'view', 'change', 'delete']:
            structured_permissions[model][action] = perm
    
    if request.method == 'POST':
        form = roleForm(request.POST, instance=role_obj)
        if form.is_valid():
            role = form.save()
            
            selected_permissions = request.POST.getlist('permissions')
            permissions = Permission.objects.filter(id__in=selected_permissions)
            
            role.permissions.set(permissions)
            
            return redirect('roleList')
        else:
            print(form.errors)
    else:
        form = roleForm(instance=role_obj)
    
    return render(request, 'role/updateRole.html', {
        'form': form,
        'structured_permissions': dict(structured_permissions),
        'role': role_obj,
    })


def deleteRole(request, pk):
    role = get_object_or_404(Role, pk=pk)
    role.delete()
    return redirect('roleList')
