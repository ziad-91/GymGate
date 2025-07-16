document.addEventListener('DOMContentLoaded', function () {
    const resultDisplay = document.getElementById('result-display');

    const syncBtn = document.getElementById('sync-btn');
    const syncStatus = document.getElementById('sync-status');

    // Track last scan to debounce duplicate readings within 5 seconds
    let lastScannedText = null;
    let lastScanTime = 0;

    const sessionSelect = document.getElementById('session-select');

    function onScanSuccess(decodedText, decodedResult) {
        // Ensure a session is chosen
        const sessionClass = sessionSelect.value;
        if (!sessionClass) {
            alert('Please choose a session before scanning.');
            return;
        }
        const now = Date.now();
        if (decodedText === lastScannedText && now - lastScanTime < 5000) {
            // Ignore duplicate scan
            return;
        }
        lastScannedText = decodedText;
        lastScanTime = now;
        console.log(`Scan result: ${decodedText}`);

        fetch('/checkin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ phone_number: decodedText, session_class: sessionClass }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Server response:', data);
            resultDisplay.textContent = data.message;
            resultDisplay.style.display = 'block';

            // Reset classes and then apply color based on acceptance
            resultDisplay.className = '';
            if (data.screen_color === 'green') {
                resultDisplay.classList.add('green-screen');
            } else {
                // Any non-green response is shown in red
                resultDisplay.classList.add('red-screen');
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            resultDisplay.textContent = 'Error checking in.';
            resultDisplay.style.display = 'block';
            resultDisplay.className = 'red-screen';
        });
    }

    function onScanError(errorMessage) {
        // handle on error condition, usually happens when camera is not available
        // console.error(`QR Code no longer in view.`);
    }

    let html5QrcodeScanner = new Html5QrcodeScanner(
        "reader", { fps: 10, qrbox: 250 });

    // Hide loading message once scanner is ready
    try {
        html5QrcodeScanner.render(onScanSuccess, onScanError);
    } catch (err) {
        console.error('Scanner render error:', err);
        alert('Failed to start scanner. Please ensure camera access is allowed.');
    }

    syncBtn.addEventListener('click', function() {
        const password = prompt("Please enter the sync password:");
        if (password) {
            syncStatus.textContent = 'Syncing...';
            fetch('/sync_airtable', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ password: password })
            })
            .then(response => response.json())
            .then(data => {
                syncStatus.textContent = data.message;
                syncStatus.style.color = data.status === 'success' ? 'green' : 'red';
            })
            .catch(error => {
                console.error('Sync error:', error);
                syncStatus.textContent = 'Sync failed.';
                syncStatus.style.color = 'red';
            });
        }
    });
});