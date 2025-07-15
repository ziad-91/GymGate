document.addEventListener('DOMContentLoaded', (event) => {
    const resultDisplay = document.getElementById('result-display');
    const loadingMessage = document.getElementById('loading-message');
    let lastScannedCode = null;
    let debounceTimer;
    const DEBOUNCE_TIME = 2000; // 2 seconds debounce time

    function onScanSuccess(decodedText, decodedResult) {
        if (decodedText !== lastScannedCode) {
            lastScannedCode = decodedText;
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                console.log(`Code matched = ${decodedText}`, decodedResult);
                sendPhoneNumberToBackend(decodedText);
            }, DEBOUNCE_TIME);
        } else {
            console.log("Duplicate scan, ignoring.");
        }
    }

    function onScanFailure(error) {
        // console.warn(`QR error = ${error}`);
    }

    let html5QrcodeScanner = new Html5Qrcode("reader");
    html5QrcodeScanner.start(
        { facingMode: "environment" }, // Prefer rear camera
        { fps: 10, qrbox: { width: 250, height: 250 } },
        onScanSuccess,
        onScanFailure
    ).then(() => {
        loadingMessage.style.display = 'none';
        console.log("QR Code scanner started.");
    }).catch((err) => {
        loadingMessage.textContent = `Error starting scanner: ${err}. Please ensure you have a webcam and grant camera permissions.`;
        loadingMessage.style.color = 'red';
        console.error("Error starting scanner:", err);
    });

    function displayResult(message, color) {
        resultDisplay.textContent = message;
        resultDisplay.className = ''; // Clear previous classes
        resultDisplay.classList.add(color === 'green' ? 'green-screen' : 'red-screen');
        resultDisplay.style.display = 'block';
        
        // Hide result after a few seconds and prepare for next scan
        setTimeout(() => {
            resultDisplay.style.display = 'none';
            resultDisplay.textContent = '';
            resultDisplay.classList.remove('green-screen', 'red-screen');
            lastScannedCode = null; // Reset last scanned code after display
        }, 5000); // Display for 5 seconds
    }

    async function sendPhoneNumberToBackend(phoneNumber) {
        try {
            const response = await fetch('/checkin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ phone_number: phoneNumber }),
            });

            const data = await response.json();
            displayResult(data.message, data.screen_color);

        } catch (error) {
            console.error('Error sending data to backend:', error);
            displayResult('Error checking in. Please try again.', 'red');
        }
    }
}); 