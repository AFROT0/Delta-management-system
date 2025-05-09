/**
 * NFC Card Reader functionality for ACR 122u using PC/SC
 * Integrates with the attendance QR page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if Web NFC API is available
    if ('NDEFReader' in window) {
        initializeNFCReader();
    } else {
        console.log("Web NFC API is not available in this browser or device");
        
        // Don't show the warning message on desktop as we have the PC/SC implementation available
        // The pcsc-nfc-reader.js will handle NFC on desktop with the ACR 122u reader
    }
});

/**
 * Initialize the NFC reader and set up event listeners
 */
function initializeNFCReader() {
    const studentIdInput = document.getElementById('student_id');
    
    // Only proceed if we're on the attendance page
    if (!studentIdInput) return;
    
    // Create status indicator
    const nfcStatusContainer = document.createElement('div');
    nfcStatusContainer.className = 'nfc-status mt-2';
    nfcStatusContainer.innerHTML = `
        <div class="alert alert-info">
            <i class="fas fa-id-card mr-2"></i>Tap your NFC student card to the reader
            <span class="nfc-status-indicator ml-2"></span>
        </div>
    `;
    
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
    
    // Start NFC scanning
    startNFCScanning();
}

/**
 * Start NFC scanning using Web NFC API
 */
function startNFCScanning() {
    const ndef = new NDEFReader();
    const nfcStatusContainer = document.querySelector('.nfc-status');
    const studentIdInput = document.getElementById('student_id');
    
    // Request permission to use NFC
    ndef.scan()
        .then(() => {
            console.log("NFC scan started successfully");
            nfcStatusContainer.querySelector('.alert').classList.add('alert-success');
            nfcStatusContainer.querySelector('.alert').classList.remove('alert-info');
            nfcStatusContainer.classList.add('nfc-active');
            
            // Update message
            nfcStatusContainer.querySelector('.alert').innerHTML = 
                '<i class="fas fa-check-circle mr-2"></i>NFC reader active. Tap your student card <span class="nfc-status-indicator ml-2"></span>';
        })
        .catch(error => {
            console.error(`Error scanning: ${error}`);
            nfcStatusContainer.querySelector('.alert').classList.add('alert-danger');
            nfcStatusContainer.querySelector('.alert').classList.remove('alert-info');
            nfcStatusContainer.classList.add('nfc-error');
            
            // Update message with error
            nfcStatusContainer.querySelector('.alert').innerHTML = 
                `<i class="fas fa-exclamation-circle mr-2"></i>Error activating NFC: ${error.message} <span class="nfc-status-indicator ml-2"></span>`;
        });
    
    // Set up reading event
    ndef.addEventListener("reading", ({ message, serialNumber }) => {
        console.log(`NFC tag read, serial number: ${serialNumber}`);
        
        let studentCode = "";
        
        // Try to read text content from NFC card
        for (const record of message.records) {
            console.log(`Record type: ${record.recordType}`);
            console.log(`MIME type: ${record.mediaType}`);
            
            // Try to decode text content
            if (record.recordType === "text") {
                const textDecoder = new TextDecoder();
                studentCode = textDecoder.decode(record.data);
                console.log(`Text content: ${studentCode}`);
            } else if (record.mediaType === "application/json" || record.recordType === "mime") {
                // Try to decode as JSON
                try {
                    const textDecoder = new TextDecoder();
                    const jsonText = textDecoder.decode(record.data);
                    const jsonData = JSON.parse(jsonText);
                    
                    // Check if it contains student_code
                    if (jsonData.student_code) {
                        studentCode = jsonData.student_code;
                        console.log(`Found student code in JSON: ${studentCode}`);
                    }
                } catch (e) {
                    console.error("Error parsing JSON from NFC tag:", e);
                }
            }
        }
        
        // If we couldn't extract structured data, use the serial number as fallback
        if (!studentCode && serialNumber) {
            studentCode = serialNumber;
            console.log(`Using serial number as student code: ${studentCode}`);
        }
        
        // Only proceed if we got a student code
        if (studentCode) {
            // Temporary visual feedback
            nfcStatusContainer.querySelector('.alert').classList.add('alert-success');
            nfcStatusContainer.querySelector('.alert').classList.remove('alert-danger', 'alert-info');
            nfcStatusContainer.querySelector('.alert').innerHTML = 
                `<i class="fas fa-check-circle mr-2"></i>Card read successfully: ${studentCode} <span class="nfc-status-indicator ml-2"></span>`;
            
            // Fill in the student ID input field
            studentIdInput.value = studentCode;
            
            // Trigger the input event to start student lookup
            studentIdInput.dispatchEvent(new Event('input', { bubbles: true }));
            
            // Reset status after 3 seconds
            setTimeout(() => {
                nfcStatusContainer.querySelector('.alert').classList.remove('alert-success');
                nfcStatusContainer.querySelector('.alert').classList.add('alert-info');
                nfcStatusContainer.querySelector('.alert').innerHTML = 
                    '<i class="fas fa-id-card mr-2"></i>Tap your NFC student card to the reader <span class="nfc-status-indicator ml-2"></span>';
            }, 3000);
        }
    });
    
    // Set up error event
    ndef.addEventListener("readingerror", ({ message }) => {
        console.error(`Error reading NFC tag: ${message}`);
        nfcStatusContainer.querySelector('.alert').classList.add('alert-danger');
        nfcStatusContainer.querySelector('.alert').classList.remove('alert-success', 'alert-info');
        nfcStatusContainer.querySelector('.alert').innerHTML = 
            `<i class="fas fa-exclamation-circle mr-2"></i>Error reading card: ${message} <span class="nfc-status-indicator ml-2"></span>`;
        
        // Reset status after 3 seconds
        setTimeout(() => {
            nfcStatusContainer.querySelector('.alert').classList.remove('alert-danger');
            nfcStatusContainer.querySelector('.alert').classList.add('alert-info');
            nfcStatusContainer.querySelector('.alert').innerHTML = 
                '<i class="fas fa-id-card mr-2"></i>Tap your NFC student card to the reader <span class="nfc-status-indicator ml-2"></span>';
        }, 3000);
    });
} 