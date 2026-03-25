
function guardarNegocio(event) {
    event.preventDefault();

    const form = document.getElementById('formNegocio');
    const formData = new FormData(form);

    fetch('', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('✅ ' + data.message);
        }
    })
    .catch(error => {
        alert('Error al guardar');
        console.error(error);
    });
}