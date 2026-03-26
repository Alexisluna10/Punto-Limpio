document.addEventListener('DOMContentLoaded', function () {

    // ── Estilos del modal (inyectados una sola vez) ──────────────────────────
    const style = document.createElement('style');
    style.textContent = `
        #qr-modal {
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.75);
            z-index: 9999;
            justify-content: center;
            align-items: center;
        }
        #qr-modal.activo {
            display: flex;
        }
        .qr-modal-box {
            background: #fff;
            border-radius: 16px;
            padding: 24px;
            max-width: 380px;
            width: 90%;
            text-align: center;
        }
        .qr-modal-titulo {
            margin: 0 0 6px 0;
            font-size: 1.2rem;
            color: #1a3a5c;
        }
        .qr-modal-subtitulo {
            margin: 0 0 16px 0;
            font-size: 0.875rem;
            color: #666;
        }
        #qr-reader {
            width: 100%;
        }
        #qr-error-msg {
            color: #e53935;
            font-size: 0.82rem;
            margin-top: 10px;
            display: none;
        }
        #qr-cancelar-btn {
            margin-top: 16px;
            background: #e0e0e0;
            border: none;
            border-radius: 8px;
            padding: 10px 28px;
            font-size: 0.95rem;
            cursor: pointer;
            color: #333;
        }
        #qr-section-btn {
            cursor: pointer;
        }
    `;
    document.head.appendChild(style);

    // ── Referencias al DOM ───────────────────────────────────────────────────
    const qrSectionBtn = document.getElementById('qr-section-btn');
    const qrModal = document.getElementById('qr-modal');
    const qrCancelarBtn = document.getElementById('qr-cancelar-btn');
    const qrErrorMsg = document.getElementById('qr-error-msg');
    const inputFolio = document.getElementById('folio');

    // Si no hay sección de escaneo en la página, salir
    if (!qrSectionBtn) return;

    let html5QrCode = null;

    // ── Abrir escáner ────────────────────────────────────────────────────────
    function abrirEscanerQR() {
        qrModal.classList.add('activo');
        qrErrorMsg.style.display = 'none';
        qrErrorMsg.textContent = '';

        html5QrCode = new Html5Qrcode('qr-reader');

        html5QrCode.start(
            { facingMode: 'environment' },
            { fps: 10, qrbox: { width: 230, height: 230 } },
            function (decodedText) {
                // Extraer folio: acepta texto plano, URL con ?folio= o URL con /rastreo/ID/
                let folio = decodedText.trim();
                try {
                    const url = new URL(decodedText);
                    const param = url.searchParams.get('folio');
                    if (param) {
                        // Caso 1: ?folio=CK-2026-ABCD
                        folio = param;
                    } else {
                        // Caso 2: URL directa como /rastreo/44/ → redirigir directo
                        cerrarEscanerQR();
                        window.location.href = decodedText;
                        return;
                    }
                } catch (e) { /* no es URL, usar texto como folio directo */ }

                cerrarEscanerQR();

                if (inputFolio) {
                    inputFolio.value = folio;
                    inputFolio.closest('form').submit();
                }
            },
            function () { /* ignorar errores de frame */ }
        ).catch(function (err) {
            qrErrorMsg.style.display = 'block';
            if (err.toString().includes('ermission') || err.toString().includes('NotAllowed')) {
                qrErrorMsg.textContent = 'Permiso de cámara denegado. Actívalo en la configuración de tu navegador.';
            } else {
                qrErrorMsg.textContent = 'No se pudo iniciar la cámara. Intenta de nuevo.';
            }
        });
    }

    // ── Cerrar escáner ───────────────────────────────────────────────────────
    function cerrarEscanerQR() {
        qrModal.classList.remove('activo');
        if (html5QrCode) {
            html5QrCode.stop().catch(function () { });
            html5QrCode = null;
        }
    }

    // ── Eventos ──────────────────────────────────────────────────────────────
    qrSectionBtn.addEventListener('click', abrirEscanerQR);
    qrCancelarBtn.addEventListener('click', cerrarEscanerQR);

    // Cerrar al hacer clic fuera del cuadro
    qrModal.addEventListener('click', function (e) {
        if (e.target === qrModal) cerrarEscanerQR();
    });

});