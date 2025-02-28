async function fetchForecast() {
    try {
        let response = await fetch('/forecast');
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        let data = await response.json();
        console.log("API Response:", data);  // Debugging

        if (data.error) {
            alert("Error fetching data: " + data.error);
            return;
        }

        const labels = ["Solar Energy", "Wind Energy"];
        const values = [data.solar_energy, data.wind_energy];

        const ctx = document.getElementById("forecastChart").getContext("2d");
        new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Predicted Energy (MW)",
                    data: values,
                    backgroundColor: ["orange", "blue"]
                }]
            }
        });
    } catch (error) {
        console.error("Fetch error:", error);
        alert("Error fetching forecast data. Check console for details.");
    }
}

window.onload = fetchForecast;
