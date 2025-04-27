document.addEventListener("DOMContentLoaded", async function () {
    const form = document.querySelector("form");

    const token = localStorage.getItem("access_token");

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const baseUrl = window.location.origin;
        const formData = new FormData(form);

        try {
            const response = await fetch(`${baseUrl}/api/users/patient/create/`, { 
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`, 
                },
                body: formData,
            });

            if (response.ok) {
                alert("Profile created successfully!");
                window.location.href = `${baseUrl}/api/users/patient-dashboard/`;
            } else {
                const errorData = await response.json();
                alert("Error saving profile: " + errorData.detail);
            }
        } catch (error) {
            console.error("Fetch Error:", error);
            alert("Something went wrong. Try again.");
        }
    });
});
