document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('formDudas');

    if (!form) return;

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const formData = new FormData(this);
        const btn = this.querySelector('button[type="submit"]');
        const btnText = btn.textContent;

        // Deshabilitar botón mientras se envía
        btn.disabled = true;
        btn.textContent = 'Enviando...';

        fetch(window.DUDAS_URL, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': window.CSRF_TOKEN
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                this.reset();
                location.reload();
            } else {
                alert('❌ Error: ' + data.message);
            }
        })
        .catch(error => {
            alert('❌ Error al enviar el comentario. Intenta de nuevo.');
            console.error('Error:', error);
        })
        .finally(() => {
            btn.disabled = false;
            btn.textContent = btnText;
        });
    });
});
