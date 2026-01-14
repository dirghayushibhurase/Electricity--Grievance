// Function to get user's current location
function getCurrentLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Geolocation is not supported by this browser.'));
        } else {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    resolve({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude
                    });
                },
                (error) => {
                    reject(error);
                }
            );
        }
    });
}

// Auto-fill latitude and longitude when raising a new issue
document.addEventListener('DOMContentLoaded', function() {
    const latitudeField = document.getElementById('latitude');
    const longitudeField = document.getElementById('longitude');
    const getLocationBtn = document.getElementById('getLocationBtn');
    
    if (getLocationBtn) {
        getLocationBtn.addEventListener('click', function() {
            getCurrentLocation()
                .then(location => {
                    if (latitudeField) latitudeField.value = location.latitude;
                    if (longitudeField) longitudeField.value = location.longitude;
                    alert('Location detected successfully!');
                })
                .catch(error => {
                    console.error('Error getting location:', error);
                    alert('Could not get your location. Please enter manually.');
                });
        });
    }
});