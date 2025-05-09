/**
 * PC/SC NFC Card Reader for ACR 122u 
 * This implementation uses server-side endpoints to communicate with the NFC reader
 * as browsers don't have direct access to PC/SC
 */

document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're on the attendance page
    if (document.getElementById('student_id')) {
        initializePCSCReader();
    }
});

/**
 * Initialize the PC/SC NFC reader interface
 */
function initializePCSCReader() {
    const studentIdInput = document.getElementById('student_id');
    
    // Create status indicator but hide it initially
    const nfcStatusContainer = document.createElement('div');
    nfcStatusContainer.className = 'nfc-status mt-2';
    nfcStatusContainer.style.display = 'none'; // Hide by default
    nfcStatusContainer.innerHTML = `
        <div class="alert alert-info">
            <i class="fas fa-id-card mr-2"></i>PC/SC NFC Reader
            <span class="nfc-status-indicator ml-2"></span>
            <button id="startNfcReading" class="btn btn-sm btn-primary ml-2">Start Reader</button>
            <button id="stopNfcReading" class="btn btn-sm btn-danger ml-2" style="display:none;">Stop Reader</button>
        </div>
    `;
    
    // Create a simple button to show the NFC reader interface
    const showReaderButton = document.createElement('button');
    showReaderButton.id = 'showNfcReader';
    showReaderButton.className = 'btn btn-outline-info btn-sm mt-2';
    showReaderButton.innerHTML = '<i class="fas fa-id-card mr-2"></i>Use NFC Reader';
    
    // Add styles for NFC status
    const style = document.createElement('style');
    style.textContent = `
        .nfc-status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: #ffc107;
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 0.4; }
            50% { opacity: 1; }
            100% { opacity: 0.4; }
        }
        
        .nfc-active .nfc-status-indicator {
            background-color: #28a745;
        }
        
        .nfc-error .nfc-status-indicator {
            background-color: #dc3545;
            animation: none;
        }
    `;
    document.head.appendChild(style);
    
    // Insert after the student ID input
    const studentIdContainer = document.getElementById('student_id').parentElement.parentElement;
    studentIdContainer.parentElement.insertBefore(nfcStatusContainer, studentIdContainer.nextSibling);
    studentIdContainer.parentElement.insertBefore(showReaderButton, studentIdContainer.nextSibling);
    
    // Show NFC reader interface when the button is clicked
    document.getElementById('showNfcReader').addEventListener('click', function() {
        nfcStatusContainer.style.display = 'block';
        showReaderButton.style.display = 'none';
    });
    
    // Add event listeners for the buttons
    document.getElementById('startNfcReading').addEventListener('click', function() {
        startPCSCReader();
        document.getElementById('startNfcReading').style.display = 'none';
        document.getElementById('stopNfcReading').style.display = 'inline-block';
    });
    
    document.getElementById('stopNfcReading').addEventListener('click', function() {
        stopPCSCReader();
        document.getElementById('startNfcReading').style.display = 'inline-block';
        document.getElementById('stopNfcReading').style.display = 'none';
    });
}

// Variable to track polling status
let isPolling = false;
let pollInterval = null;

/**
 * Start the PC/SC NFC reader polling
 */
function startPCSCReader() {
    const nfcStatusContainer = document.querySelector('.nfc-status');
    nfcStatusContainer.classList.add('nfc-active');
    nfcStatusContainer.querySelector('.alert').classList.add('alert-success');
    nfcStatusContainer.querySelector('.alert').classList.remove('alert-info', 'alert-danger');
    
    // Update status message
    const statusText = nfcStatusContainer.querySelector('.alert');
    statusText.innerHTML = `
        <i class="fas fa-spinner fa-spin mr-2"></i>Initializing NFC reader...
        <span class="nfc-status-indicator ml-2"></span>
        <button id="stopNfcReading" class="btn btn-sm btn-danger ml-2">Stop Reader</button>
    `;
    
    // Verify the reader is connected by checking the endpoint
    fetch('/api/nfc/status/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Reader is connected
            statusText.innerHTML = `
                <i class="fas fa-check-circle mr-2"></i>NFC reader connected: ${data.reader_name}
                <span class="nfc-status-indicator ml-2"></span>
                <button id="stopNfcReading" class="btn btn-sm btn-danger ml-2">Stop Reader</button>
            `;
            
            // Start polling for cards
            isPolling = true;
            pollForCards();
            
            // Re-add the event listener to the stop button (as we replaced the HTML)
            document.getElementById('stopNfcReading').addEventListener('click', function() {
                stopPCSCReader();
                document.getElementById('startNfcReading').style.display = 'inline-block';
                document.getElementById('stopNfcReading').style.display = 'none';
            });
        } else {
            // Reader not connected - show more discreet error
            nfcStatusContainer.classList.remove('nfc-active');
            nfcStatusContainer.classList.add('nfc-error');
            statusText.innerHTML = `
                <i class="fas fa-exclamation-circle mr-2"></i>NFC reader not found
                <span class="nfc-status-indicator ml-2"></span>
                <button id="startNfcReading" class="btn btn-sm btn-primary ml-2">Retry</button>
            `;
            
            // Log detailed error to console instead of showing it to user
            console.error(`NFC reader error: ${data.message}`);
            
            // Re-add the event listener
            document.getElementById('startNfcReading').addEventListener('click', function() {
                startPCSCReader();
            });
        }
    })
    .catch(error => {
        // Connection error - show more discreet error message
        console.error('Error checking reader status:', error);
        nfcStatusContainer.classList.remove('nfc-active');
        nfcStatusContainer.classList.add('nfc-error');
        statusText.innerHTML = `
            <i class="fas fa-exclamation-circle mr-2"></i>Connection error
            <span class="nfc-status-indicator ml-2"></span>
            <button id="startNfcReading" class="btn btn-sm btn-primary ml-2">Retry</button>
        `;
        
        // Re-add the event listener
        document.getElementById('startNfcReading').addEventListener('click', function() {
            startPCSCReader();
        });
    });
}

/**
 * Stop the PC/SC NFC reader polling
 */
function stopPCSCReader() {
    // Stop the polling
    isPolling = false;
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
    
    // Update UI
    const nfcStatusContainer = document.querySelector('.nfc-status');
    nfcStatusContainer.classList.remove('nfc-active', 'nfc-error');
    nfcStatusContainer.querySelector('.alert').classList.remove('alert-success', 'alert-danger');
    nfcStatusContainer.querySelector('.alert').classList.add('alert-info');
    
    // Reset the message
    nfcStatusContainer.querySelector('.alert').innerHTML = `
        <i class="fas fa-id-card mr-2"></i>PC/SC NFC Reader
        <span class="nfc-status-indicator ml-2"></span>
        <button id="startNfcReading" class="btn btn-sm btn-primary ml-2">Start Reader</button>
    `;
    
    // Re-add the event listener
    document.getElementById('startNfcReading').addEventListener('click', function() {
        startPCSCReader();
        document.getElementById('startNfcReading').style.display = 'none';
        document.getElementById('stopNfcReading').style.display = 'inline-block';
    });
    
    // Send request to stop reading at the server
    fetch('/api/nfc/stop/', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .catch(error => {
        console.error('Error stopping NFC reader:', error);
    });
}

/**
 * Poll for NFC cards
 */
function pollForCards() {
    if (!isPolling) return;
    
    // Set up interval to poll for cards
    pollInterval = setInterval(() => {
        if (!isPolling) {
            clearInterval(pollInterval);
            return;
        }
        
        // Send request to read card
        fetch('/api/nfc/read/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.card_data) {
                handleCardData(data.card_data, data.card_id);
            }
        })
        .catch(error => {
            // Just log to console, don't show error to user
            console.error('Error polling for NFC card:', error);
        });
    }, 1000); // Poll every second
}

/**
 * Handle card data received from the server
 */
function handleCardData(cardData, cardId) {
    const studentIdInput = document.getElementById('student_id');
    const nfcStatusContainer = document.querySelector('.nfc-status');
    
    // Extract student code from the card data
    let studentCode = "";
    
    // First try to parse as JSON
    try {
        const jsonData = JSON.parse(cardData);
        if (jsonData.student_code) {
            studentCode = jsonData.student_code;
        }
    } catch (e) {
        // If not JSON, use the raw text or card ID
        studentCode = cardData || cardId;
    }
    
    if (studentCode) {
        // Update the status
        nfcStatusContainer.querySelector('.alert').innerHTML = `
            <i class="fas fa-check-circle mr-2"></i>Card read successfully
            <span class="nfc-status-indicator ml-2"></span>
            <button id="stopNfcReading" class="btn btn-sm btn-danger ml-2">Stop Reader</button>
        `;
        
        // Fill in the student ID input field
        studentIdInput.value = studentCode;
        
        // Trigger the input event to start student lookup
        studentIdInput.dispatchEvent(new Event('input', { bubbles: true }));
        
        // Pause polling briefly to avoid multiple reads
        isPolling = false;
        clearInterval(pollInterval);
        
        // Re-add the event listener to the stop button
        document.getElementById('stopNfcReading').addEventListener('click', function() {
            stopPCSCReader();
            document.getElementById('startNfcReading').style.display = 'inline-block';
            document.getElementById('stopNfcReading').style.display = 'none';
        });
        
        // Resume polling after a delay
        setTimeout(() => {
            if (!isPolling) {
                isPolling = true;
                pollForCards();
            }
        }, 3000);
    }
} 