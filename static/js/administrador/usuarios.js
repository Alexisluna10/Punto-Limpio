
function filterTable() {
    const filter = document.getElementById('searchInput').value.toLowerCase();
    const table  = document.getElementById('tablaUsuarios');
    const rows   = table.getElementsByTagName('tr');

    for (let i = 1; i < rows.length; i++) {
        const cells = rows[i].getElementsByTagName('td');
        let found   = false;

        for (let j = 0; j < cells.length; j++) {
            if (cells[j].textContent.toLowerCase().includes(filter)) {
                found = true;
                break;
            }
        }

        rows[i].style.display = found ? '' : 'none';
    }
}

function abrirModalEditar(usuarioId) {
    fetch('/panel-admin/usuarios/editar/' + usuarioId + '/', {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('modalUsername').textContent          = data.username + ' (' + data.rol + ')';
        document.getElementById('edit_first_name').value              = data.first_name;
        document.getElementById('edit_last_name').value               = data.last_name;
        document.getElementById('edit_telefono').value                = data.telefono;
        document.getElementById('edit_email').value                   = data.email;
        document.getElementById('edit_password').value                = '';
        document.getElementById('formEditarUsuario').action           = '/panel-admin/usuarios/editar/' + data.id + '/';
        document.getElementById('modalEditarUsuario').classList.add('active');
    })
    .catch(() => { alert('Error al cargar los datos del usuario.'); });
}

function cerrarModalEditar() {
    document.getElementById('modalEditarUsuario').classList.remove('active');
}

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('modalEditarUsuario').addEventListener('click', function (e) {
        if (e.target === this) cerrarModalEditar();
    });
});