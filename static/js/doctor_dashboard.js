document.addEventListener("DOMContentLoaded", function () {
    lucide.createIcons(); // Initialize icons

    const token = localStorage.getItem("access_token");
    const baseUrl = window.location.origin;
    let currentPage = 1;
    let currentPatientId = null; // Track the currently selected patient
    let doctorProfile = null;
    let patientsList = [];
    let doctorId = null; // Add doctorId declaration

    // Fetch Doctor Profile
    let doctorUsername = "";
    async function fetchDoctorProfile() {
        try {
            const response = await fetch(`${baseUrl}/api/users/doctor/profile/`, {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            });

            if (!response.ok) throw new Error("Failed to fetch doctor profile");

            const data = await response.json();
            
            console.log("Doctor Profile:", data);

            // Update Doctor Details
            doctorUsername = data.user?.username || "N/A";
            document.getElementById("doctor-name").innerText = doctorUsername;
            document.getElementById("specialization").innerText = data.specialization || "N/A";
            document.getElementById("hospital-name").innerText = data.hospital?.name || "N/A";
            document.getElementById("consultation-fee").innerText = data.consultation_fee || "N/A";
            document.getElementById("profile-picture").src = data.profile_picture || "https://via.placeholder.com/100";
            document.getElementById("phone").innerText = data.user?.phone || "N/A";
            document.getElementById("email").innerText = data.user?.email || "N/A";
            doctorId = data.id; // Set doctorId
        } catch (error) {
            console.error("Error fetching doctor profile:", error);
        }
    }

    // Helper function to calculate age from date of birth
    function calculateAge(dateOfBirth) {
        const today = new Date();
        const birthDate = new Date(dateOfBirth);
        let age = today.getFullYear() - birthDate.getFullYear();
        const monthDiff = today.getMonth() - birthDate.getMonth();
        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
            age--;
        }
        return age;
    }

    // Show Patient Details
    function showPatientDetails(patient) {
        const modal = document.getElementById("patient-modal");

        // Update Patient Details
        document.getElementById("patient-profile-pic").src = patient.profile_picture || "https://via.placeholder.com/100";
        document.getElementById("patient-name").innerText = `${patient.user.first_name} ${patient.user.last_name}`;
        document.getElementById("patient-age-gender").innerText = `${patient.gender}, ${calculateAge(patient.date_of_birth)} years`;
        document.getElementById("patient-blood-type").innerText = `Blood Type: ${patient.blood_type || "N/A"}`;
        document.getElementById("patient-medical-history").innerText = patient.medical_history?.diagnosis || "No diagnosis available";
        document.getElementById("patient-medications").innerHTML = patient.current_medications?.map(med => `<li>${med.name} (${med.dosage}) - ${med.prescribed_by}</li>`).join("") || "No medications prescribed";

        const doctorsList = document.getElementById("patient-doctors");
        doctorsList.innerHTML = ""; // Clear previous content

        if (patient.doctors && patient.doctors.length > 0) {
            patient.doctors.forEach(doctor => {
                if (doctor) {
                    const li = document.createElement("li");
                    li.innerHTML = `Dr. ${doctor.first_name || "N/A"} ${doctor.last_name || "N/A"} (${doctor.specialization || "N/A"})`;
                    doctorsList.appendChild(li);
                } else {
                    const li = document.createElement("li");
                    li.innerHTML = "Invalid doctor data";
                    doctorsList.appendChild(li);
                }
            });
        } else {
            doctorsList.innerHTML = "<li>No doctors assigned</li>";
        }

        // Set currentPatientId
        currentPatientId = patient.id;
        // Show the modal
        modal.classList.remove("hidden");

        // Add event listener to the "Start Messaging" button
        const startMessagingButton = document.getElementById("start-messaging");
        startMessagingButton.onclick = () => startMessaging(patient.user.username);
    }

    // Function to start messaging
    function startMessaging(patientUsername) {
        // Redirect to the chat start URL which handles authentication and conversation creation
        window.location.href = `${baseUrl}/api/messaging/conversations/`;
    }

    // Fetch Patients List
    async function fetchPatients(page = 1) {
        try {
            const response = await fetch(`${baseUrl}/api/users/doctor/patients/?page=${page}`, {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            });

            if (!response.ok) throw new Error("Failed to fetch patients");

            const data = await response.json();
            console.log("Patients data:", data);

            const patientsList = document.getElementById("patients-list");
            patientsList.innerHTML = "";

            if (!data.results || data.results.length === 0) {
                patientsList.innerHTML = "<li class='text-gray-600 p-2'>No patients found</li>";
                return;
            }

            // Update Total Patients
            document.getElementById("total-patients").innerText = data.count || 0;

            // Display Patients
            data.results.forEach(patient => {
                let li = document.createElement("li");
                li.classList.add("p-2", "flex", "items-center", "cursor-pointer", "hover:bg-gray-50");
                li.innerHTML = `
                    <i data-lucide="user" class="w-5 h-5 mr-2 text-gray-600"></i>
                    <div>
                        <p class="font-semibold">${patient.user.username}</p>
                        <p class="text-sm text-gray-600">${patient.gender}, ${calculateAge(patient.date_of_birth)} years</p>
                    </div>
                `;
                li.addEventListener("click", () => showPatientDetails(patient));
                patientsList.appendChild(li);
            });

            // Load Charts with Fetched Data
            loadCharts(data.results);

        } catch (error) {
            console.error("Error fetching patients:", error);
        }
    }

    // Load Charts
    function loadCharts(patients) {
        if (!patients || patients.length === 0) {
            console.error("No patients data available for charts");
            return;
        }

        // Normalize and Calculate Gender Distribution
        const genderCounts = {
            Male: 0,
            Female: 0,
            Other: 0
        };

        patients.forEach(patient => {
            const gender = patient.gender?.trim().toLowerCase(); // Normalize gender value
            if (gender === "male") {
                genderCounts.Male++;
            } else if (gender === "female") {
                genderCounts.Female++;
            } else {
                genderCounts.Other++;
            }
        });

        // Calculate Age Distribution
        const ageGroups = {
            "0-18": 0,
            "19-35": 0,
            "36-50": 0,
            "51+": 0
        };

        patients.forEach(patient => {
            const age = calculateAge(patient.date_of_birth); // Calculate age from date of birth
            if (age <= 18) ageGroups["0-18"]++;
            else if (age <= 35) ageGroups["19-35"]++;
            else if (age <= 50) ageGroups["36-50"]++;
            else ageGroups["51+"]++;
        });

        // Patients by Gender Chart
        const genderCtx = document.getElementById("patientsChart").getContext("2d");
        new Chart(genderCtx, {
            type: "doughnut",
            data: {
                labels: ["Males", "Females", "Others"],
                datasets: [{
                    data: [genderCounts.Male, genderCounts.Female, genderCounts.Other],
                    backgroundColor: ["#1E3A8A", "#F87171", "#10B981"]
                }]
            }
        });

        // Age Distribution Chart
        const ageCtx = document.getElementById("ageChart").getContext("2d");
        new Chart(ageCtx, {
            type: "bar",
            data: {
                labels: ["0-18", "19-35", "36-50", "51+"],
                datasets: [{
                    label: "Patients",
                    data: [ageGroups["0-18"], ageGroups["19-35"], ageGroups["36-50"], ageGroups["51+"]],
                    backgroundColor: "#1E3A8A"
                }]
            }
        });
    }

    // Close Modal
    document.getElementById("close-modal").addEventListener("click", () => {
        document.getElementById("patient-modal").classList.add("hidden");
    });

    // Search Patients
    document.getElementById("search-bar").addEventListener("input", (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const patientsList = document.getElementById("patients-list");
        const patients = Array.from(patientsList.children);

        patients.forEach(patient => {
            const patientName = patient.querySelector(".font-semibold").innerText.toLowerCase();
            if (patientName.includes(searchTerm)) {
                patient.classList.remove("hidden");
            } else {
                patient.classList.add("hidden");
            }
        });
    });

document.getElementById('write-prescription').addEventListener("click", function () {
    console.log("Opening prescription form");
    document.getElementById('prescription-form').classList.toggle("hidden");
});

document.getElementById('prescriptionForm').addEventListener("submit", async function (event) {
    event.preventDefault(); // Prevent page reload

    if (!doctorId || !currentPatientId) {
        alert("Doctor or patient ID is missing!");
        return;
    }

    const medicine = document.getElementById('medicine').value;
    const dosage = document.getElementById('dosage').value;
    const notes = document.getElementById('notes').value;

    // Check for empty fields
    if (!medicine || !dosage) {
        alert("Medicine and dosage are required!");
        return;
    }

    // Combine medicine, dosage, and notes into a single object
    const prescriptionDetails = {
        medicine: medicine,
        dosage: dosage,
        notes: notes
    };

    // Encrypt the prescription details using CryptoJS
    let encryptedPrescription;
    try {
        const prescriptionString = JSON.stringify(prescriptionDetails);
        encryptedPrescription = CryptoJS.AES.encrypt(prescriptionString, 'your-secret-key').toString();
    } catch (err) {
        console.error("Encryption failed:", err);
        alert("Failed to encrypt prescription data!");
        return;
    }

    // Prepare prescription data
    const prescriptionData = {
        patient: currentPatientId, // Use 'patient' instead of 'patient_name'
        doctor: doctorId, // Use 'doctor' instead of 'doctor_name'
        encrypted_prescription: encryptedPrescription // Send encrypted data
    };

    try {
        const response = await fetch(`${baseUrl}/api/prescriptions/create/`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify(prescriptionData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error("API Error:", errorData);
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Prescription submitted:", data);
        alert("Prescription submitted successfully!");

        // Clear form and hide it
        document.getElementById('prescriptionForm').reset();
        document.getElementById('prescription-form').classList.add("hidden");
    } catch (err) {
        console.error("Error submitting prescription:", err);
        alert("Failed to submit prescription!");
    }
});




// Elements
const viewAppointmentsBtn = document.getElementById("view-appointments");
const appointmentsContainer = document.getElementById("appointments-container");
const appointmentsList = document.getElementById("appointments-list");

let appointmentId = ""; // Use let instead of const

// Check if the patient has appointments
async function hasAppointment(patientId) {
    try {
        const response = await fetch(`${baseUrl}/api/appointments/patients/${currentPatientId}/has-appointments/`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.has_appointments && data.id) {
            appointmentId = data.id; // Assign appointment ID
        }
        
        return data.has_appointments;
    } catch (error) {
        console.error("Error checking appointments:", error);
        alert("Failed to check appointments. Please try again.");
        return false; // Default to false in case of error
    }
}

// Fetch appointments for the patient
async function fetchAppointments() {
    if (!appointmentId) {
        console.error("No appointment ID available.");
        return;
    }

    try {
        const response = await fetch(`${baseUrl}/api/appointments/appointments/${appointmentId}/`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        console.log("API Response:", data); // Log the response

        // If API response is an object and not a list, wrap it in an array
        const appointments = Array.isArray(data) ? data : [data];

        renderAppointments(appointments);
    } catch (error) {
        console.error("Error fetching appointments:", error);
        alert("Failed to fetch appointments. Please try again.");
    }
}

// Render appointments in the HTML
function renderAppointments(appointments) {
    if (!appointments || appointments.length === 0) {
        appointmentsList.innerHTML = "<p class='text-gray-600'>No appointments found for this patient.</p>";
        return;
    }

    appointmentsList.innerHTML = appointments
        .map(
            (appointment) => `
        <div class="bg-white p-6 rounded-lg shadow-md">
            <div class="flex justify-between items-center">
                <div>
                    <h3 class="text-xl font-semibold">Appointment #${appointment.id}</h3>
                    <p class="text-gray-600">${appointment.date} at ${appointment.time}</p>
                </div>
                <span class="px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(appointment.status)}">
                    ${appointment.status}
                </span>
            </div>
            <div class="mt-4">
                <p class="text-gray-700"><span class="font-semibold">Patient:</span> ${appointment.patient_name}</p>
                <p class="text-gray-700"><span class="font-semibold">Doctor:</span> ${appointment.doctor_name}</p>
                <p class="text-gray-700"><span class="font-semibold">Hospital:</span> ${appointment.hospital_name}</p>
            </div>
        </div>
    `
        )
        .join("");
}

// Helper function to get status color
function getStatusColor(status) {
    switch (status.toLowerCase()) {
        case "pending":
            return "bg-yellow-100 text-yellow-800";
        case "completed":
            return "bg-green-100 text-green-800";
        case "cancelled":
            return "bg-red-100 text-red-800";
        default:
            return "bg-gray-100 text-gray-800";
    }
}

// Show appointments when the button is clicked
viewAppointmentsBtn.addEventListener("click", async function () {
    const hasAppointments = await hasAppointment(currentPatientId);

    if (hasAppointments) {
        appointmentsContainer.classList.remove("hidden");
        await fetchAppointments();
    } else {
        appointmentsList.innerHTML = "<p class='text-gray-600'>No appointments found for this patient.</p>";
        appointmentsContainer.classList.remove("hidden"); // Show the container even if no appointments exist
    }
});



const writeReportBtn = document.getElementById("write-report");
const reportModal = document.getElementById("report-modal");
const closeModalBtn = document.getElementById("close-modal");
const reportForm = document.getElementById("report-form");

// Open modal
writeReportBtn.addEventListener("click", function () {
    reportModal.classList.remove("hidden");
});

// Close modal
closeModalBtn.addEventListener("click", function () {
    reportModal.classList.add("hidden");
});

// Submit medical report form
reportForm.addEventListener("submit", async function (event) {
    event.preventDefault(); // Prevent page reload

    // Get values from form
    const diagnosis = document.getElementById("diagnosis").value;
    const treatment = document.getElementById("treatment").value;
    const notes = document.getElementById("notes").value;
    const fileInput = document.getElementById("report-file").files[0];
    const appointment = document.getElementById("appointment-id").value || null;
    
    // Encrypt notes (Make sure encryptAES is defined!)
    const encryptedNotes = typeof encryptAES === "function" ? encryptAES(notes) : notes;

    // Create FormData for file upload
    const formData = new FormData();
    formData.append("patient", currentPatientId);
    formData.append("doctor", doctorId);
    formData.append("diagnosis", diagnosis);
    formData.append("treatment_plan", treatment);
    formData.append("encrypted_notes", encryptedNotes);
    if (fileInput) formData.append("report_file", fileInput);
    if (appointment) formData.append("appointment", appointment);

    try {
        const response = await fetch(`${baseUrl}/api/prescriptions/medical-report/create/`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` }, // Auth token
            body: formData // Send file & text
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error("API Error:", errorData);
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Medical report submitted:", data);
        alert("Medical report submitted successfully!");

        // Close modal & reset form
        reportModal.classList.add("hidden");
        reportForm.reset();
    } catch (err) {
        console.error("Error submitting medical report:", err);
        alert("Failed to submit medical report!");
    }
});


    // Initialize Dashboard
    fetchDoctorProfile();
    fetchPatients(); // This will call loadCharts internally
});