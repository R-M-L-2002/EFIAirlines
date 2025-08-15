// static/js/seat_selection.js

let selectedSeatElement = null;

// Verifica si un asiento está disponible
function checkAvailability(seatDiv) {
    return !seatDiv.classList.contains('occupied');
}

// Selecciona un asiento
function selectSeat(element) {
    if (!checkAvailability(element)) {
        alert("This seat is not available.");
        return;
    }

    // Deselecciona asiento anterior
    if (selectedSeatElement) {
        selectedSeatElement.classList.remove('selected');
    }

    element.classList.add('selected');
    selectedSeatElement = element;

    // Actualiza input oculto para enviar al servidor
    const seatInput = document.getElementById('selectedSeat');
    if (seatInput) {
        seatInput.value = element.dataset.seatId;
    }

    // Habilita el botón de reserva
    const btnReserve = document.getElementById('btnReserve');
    if (btnReserve) {
        btnReserve.disabled = false;
    }

    // Actualiza panel lateral con info del asiento
    updateSeatInfo(element);
}

// Actualiza información del asiento seleccionado
function updateSeatInfo(element) {
    const infoPanel = document.getElementById('seatInfo');
    const price = parseFloat(element.dataset.price);

    infoPanel.innerHTML = `
        <div class="text-center">
            <div class="seat ${element.classList[1]} ${element.classList[2]} mb-3" 
                 style="font-size: 16px; width: 60px; height: 60px;">
                ${element.dataset.number}
            </div>
            <h5>Seat ${element.dataset.number}</h5>
            <p class="mb-2"><strong>Class:</strong> ${element.dataset.type}</p>
            <h4 class="text-success mb-3">$${price.toFixed(2)}</h4>
            
            <div class="alert alert-info">
                <small>
                    <i class="fas fa-info-circle"></i>
                    ${getClassInfo(element.classList[2])}
                </small>
            </div>
        </div>
    `;
}

// Devuelve info según clase
function getClassInfo(className) {
    switch(className) {
        case 'first':
            return 'Includes: Gourmet meal, premium drinks, reclining seat, extra baggage.';
        case 'business':
            return 'Includes: Enhanced meal, drinks, comfortable seat, additional baggage.';
        case 'economy':
            return 'Includes: Snack, drink, standard carry-on baggage.';
        default:
            return 'Standard class.';
    }
}

// Inicializa eventos y tooltips al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.seat.available').forEach(seat => {
        seat.addEventListener('click', function() {
            selectSeat(this);
        });
        // Tooltip con precio
        seat.title = `Price: $${parseFloat(seat.dataset.price).toFixed(2)}`;
    });
});
