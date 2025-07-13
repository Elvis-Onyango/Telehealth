document.addEventListener("DOMContentLoaded", function () {
    lucide.createIcons(); // Initialize icons

    // Constants and Variables
    const token = localStorage.getItem("access_token");
    const baseUrl = window.location.origin;
    let currentPage = 1;
    let currentPatientId = null;
    let doctorProfile = null;
    let patientsList = [];
    let doctorId = null;
    let doctorUsername = "";

    // DOM Elements
    const profileViewBtn = document.getElementById("view-profile");
    const profileEditBtn = document.getElementById("edit-profile");
    const profileContainer = document.getElementById("profile-container");
    const profileForm = document.getElementById("profile-form");
    const profileViewContent = document.getElementById("profile-view-content");
    const profileEditContent = document.getElementById("profile-edit-content");
    const profilePicInput = document.getElementById("profile_picture");
    const profilePicPreview = document.getElementById("profile-picture-preview");
    const searchBar = document.getElementById("search-bar");
    const patientsListElement = document.getElementById("patients-list");
    const viewAppointmentsBtn = document.getElementById("view-appointments");
    const appointmentsContainer = document.getElementById("appointments-container");
    const appointmentsList = document.getElementById("appointments-list");
    const writePrescriptionBtn = document.getElementById("write-prescription");
    const prescriptionFormContainer = document.getElementById("prescription-form");
    const prescriptionForm = document.getElementById("prescriptionForm");
    const writeReportBtn = document.getElementById("write-report");
    const reportModal = document.getElementById("report-modal");
    const closeModalBtn = document.getElementById("close-modal");
    const reportForm = document.getElementById("report-form");

    // Initialize the dashboard
    initDashboard();

    async function initDashboard() {
        await fetchDoctorProfile();
        await fetchPatients();
        setupEventListeners();
        profileViewBtn.click(); // Start in view mode
    }

    // Fetch Doctor Profile
    async function fetchDoctorProfile() {
        try {
            const response = await fetch(`${baseUrl}/api/users/doctor/profile`, {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            });

            if (!response.ok) throw new Error("Failed to fetch doctor profile");

            const data = await response.json();
            console.log("Doctor profile response:", data);
            doctorProfile = data;
            doctorId = data.id;
            doctorUsername = data.user?.username || "N/A";
            
            // Update UI elements
            if (document.getElementById("doctor-name")) {
                document.getElementById("doctor-name").innerText = doctorUsername;
                document.getElementById("specialization").innerText = data.specialization || "N/A";
                document.getElementById("hospital-name").innerText = data.hospital?.name || "N/A";
                document.getElementById("consultation-fee").innerText = data.consultation_fee || "N/A";
                document.getElementById("profile-picture").src = data.profile_picture || "https://via.placeholder.com/100";
                document.getElementById("phone").innerText = data.user?.phone || "N/A";
                document.getElementById("email").innerText = data.user?.email || "N/A";
            }
            
            // Update profile view if it exists
            if (profileViewContent) {
                renderProfileView(data);
                populateEditForm(data);
            }
            
        } catch (error) {
            console.error("Error fetching doctor profile:", error);
            showToast("Failed to load profile", "error");
        }
    }

    // Render Profile View
    function renderProfileView(profile) {
        if (!profileViewContent) return;
        
        profileViewContent.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-lg font-semibold mb-4">Personal Information</h3>
                    <div class="space-y-4">
                        <div>
                            <p class="text-sm text-gray-500">Full Name</p>
                            <p class="font-medium">${profile.user.first_name} ${profile.user.last_name}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-500">Email</p>
                            <p class="font-medium">${profile.user.email}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-500">Phone</p>
                            <p class="font-medium">${profile.user.phone || 'Not provided'}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-500">Gender</p>
                            <p class="font-medium">${profile.user.gender || 'Not specified'}</p>
                        </div>
                    </div>
                </div>

                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-lg font-semibold mb-4">Professional Information</h3>
                    <div class="space-y-4">
                        <div>
                            <p class="text-sm text-gray-500">Specialization</p>
                            <p class="font-medium">${profile.specialization}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-500">Hospital</p>
                            <p class="font-medium">${profile.hospital?.name || 'Not specified'}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-500">License Number</p>
                            <p class="font-medium">${profile.license_number}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-500">Consultation Fee</p>
                            <p class="font-medium">$${profile.consultation_fee}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-500">Years of Experience</p>
                            <p class="font-medium">${profile.years_of_experience}</p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="mt-6 bg-white rounded-lg shadow p-6">
                <h3 class="text-lg font-semibold mb-4">Availability</h3>
                ${renderAvailability(profile.available_days)}
            </div>
        `;
    }

    function renderAvailability(availableDays) {
        if (!availableDays || availableDays.length === 0) {
            return '<p class="text-gray-500">No availability set</p>';
        }

        const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        return `
            <div class="grid grid-cols-2 md:grid-cols-7 gap-2">
                ${days.map(day => `
                    <div class="p-2 rounded text-center ${availableDays.some(d => d.day.toLowerCase() === day.toLowerCase()) 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-gray-100 text-gray-500'}">
                        ${day.substring(0, 3)}
                    </div>
                `).join('')}
            </div>
        `;
    }

    // Populate Edit Form
    function populateEditForm(profile) {
        if (!profileForm) return;
        
        document.getElementById("first_name").value = profile.user.first_name;
        document.getElementById("last_name").value = profile.user.last_name;
        document.getElementById("email").value = profile.user.email;
        document.getElementById("phone").value = profile.user.phone || '';
        document.getElementById("gender").value = profile.user.gender || '';
        document.getElementById("specialization").value = profile.specialization;
        document.getElementById("license_number").value = profile.license_number;
        document.getElementById("consultation_fee").value = profile.consultation_fee;
        document.getElementById("years_of_experience").value = profile.years_of_experience;
        
        // Set hospital select
        if (profile.hospital && document.getElementById("hospital")) {
            document.getElementById("hospital").value = profile.hospital.id;
        }
        
        // Set available days checkboxes
        if (profile.available_days) {
            profile.available_days.forEach(day => {
                const checkbox = document.querySelector(`input[name="available_days"][value="${day.id}"]`);
                if (checkbox) checkbox.checked = true;
            });
        }
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
            patientsList = data.results || [];

            // Update Total Patients
            if (document.getElementById("total-patients")) {
                document.getElementById("total-patients").innerText = data.count || 0;
            }

            // Display Patients
            renderPatientsList(patientsList);
            
            // Load Charts with Fetched Data
            loadCharts(patientsList);

        } catch (error) {
            console.error("Error fetching patients:", error);
            showToast("Failed to load patients", "error");
        }
    }

    function renderPatientsList(patients) {
        if (!patientsListElement) return;
        
        patientsListElement.innerHTML = "";

        if (!patients || patients.length === 0) {
            patientsListElement.innerHTML = "<li class='text-gray-600 p-2'>No patients found</li>";
            return;
        }

        patients.forEach(patient => {
            const li = document.createElement("li");
            li.classList.add("p-2", "flex", "items-center", "cursor-pointer", "hover:bg-gray-50");
            li.innerHTML = `
                <i data-lucide="user" class="w-5 h-5 mr-2 text-gray-600"></i>
                <div>
                    <p class="font-semibold">${patient.user.first_name} ${patient.user.last_name}</p>
                    <p class="text-sm text-gray-600">${patient.gender}, ${calculateAge(patient.date_of_birth)} years</p>
                </div>
            `;
            li.addEventListener("click", () => showPatientDetails(patient));
            patientsListElement.appendChild(li);
        });

        // Refresh Lucide icons
        lucide.createIcons();
    }

    // Show Patient Details
    function showPatientDetails(patient) {
        const modal = document.getElementById("patient-modal");
        if (!modal) return;

        // Update Patient Details
        document.getElementById("patient-profile-pic").src = patient.profile_picture || "https://via.placeholder.com/100";
        document.getElementById("patient-name").innerText = `${patient.user.first_name} ${patient.user.last_name}`;
        document.getElementById("patient-age-gender").innerText = `${patient.gender}, ${calculateAge(patient.date_of_birth)} years`;
        document.getElementById("patient-blood-type").innerText = `Blood Type: ${patient.blood_type || "N/A"}`;
        document.getElementById("patient-medical-history").innerText = patient.medical_history?.diagnosis || "No diagnosis available";
        document.getElementById("patient-medications").innerHTML = 
            patient.current_medications?.map(med => `<li>${med.name} (${med.dosage}) - ${med.prescribed_by}</li>`).join("") || 
            "No medications prescribed";

        const doctorsList = document.getElementById("patient-doctors");
        if (doctorsList) {
            doctorsList.innerHTML = "";
            if (patient.doctors && patient.doctors.length > 0) {
                patient.doctors.forEach(doctor => {
                    if (doctor) {
                        const li = document.createElement("li");
                        li.innerHTML = `Dr. ${doctor.first_name || "N/A"} ${doctor.last_name || "N/A"} (${doctor.specialization || "N/A"})`;
                        doctorsList.appendChild(li);
                    }
                });
            } else {
                doctorsList.innerHTML = "<li>No doctors assigned</li>";
            }
        }

        // Set currentPatientId
        currentPatientId = patient.id;
        // Show the modal
        modal.classList.remove("hidden");
    }

    // Load Charts
    function loadCharts(patients) {
        if (!patients || patients.length === 0) return;

        // Gender Distribution
        const genderCounts = { Male: 0, Female: 0, Other: 0 };
        patients.forEach(patient => {
            const gender = patient.gender?.trim().toLowerCase();
            if (gender === "male") genderCounts.Male++;
            else if (gender === "female") genderCounts.Female++;
            else genderCounts.Other++;
        });

        // Age Distribution
        const ageGroups = { "0-18": 0, "19-35": 0, "36-50": 0, "51+": 0 };
        patients.forEach(patient => {
            const age = calculateAge(patient.date_of_birth);
            if (age <= 18) ageGroups["0-18"]++;
            else if (age <= 35) ageGroups["19-35"]++;
            else if (age <= 50) ageGroups["36-50"]++;
            else ageGroups["51+"]++;
        });

        // Patients by Gender Chart
        const genderCtx = document.getElementById("patientsChart")?.getContext("2d");
        if (genderCtx) {
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
        }

        // Age Distribution Chart
        const ageCtx = document.getElementById("ageChart")?.getContext("2d");
        if (ageCtx) {
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
    }

    // Helper function to calculate age from date of birth
    function calculateAge(dateOfBirth) {
        if (!dateOfBirth) return "N/A";
        const today = new Date();
        const birthDate = new Date(dateOfBirth);
        let age = today.getFullYear() - birthDate.getFullYear();
        const monthDiff = today.getMonth() - birthDate.getMonth();
        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
            age--;
        }
        return age;
    }

    // Handle Profile Form Submission
    async function handleProfileUpdate(e) {
        e.preventDefault();
        
        const formData = new FormData(profileForm);
        const availableDays = Array.from(document.querySelectorAll('input[name="available_days"]:checked'))
                                .map(checkbox => checkbox.value);
        
        availableDays.forEach(day => formData.append('available_days', day));

        try {
            const response = await fetch(`${baseUrl}/api/users/doctor/profile/update`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` },
                body: formData
            });

            if (!response.ok) throw new Error("Failed to update profile");

            const data = await response.json();
            doctorProfile = data;
            renderProfileView(data);
            profileViewBtn.click();
            showToast("Profile updated successfully", "success");
            
        } catch (error) {
            console.error("Error updating profile:", error);
            showToast("Failed to update profile", "error");
        }
    }

    // Handle Prescription Form Submission
    async function handlePrescriptionSubmit(e) {
        e.preventDefault();

        if (!doctorId || !currentPatientId) {
            showToast("Doctor or patient ID is missing!", "error");
            return;
        }

        const medicine = document.getElementById('medicine').value;
        const dosage = document.getElementById('dosage').value;
        const notes = document.getElementById('notes').value;

        if (!medicine || !dosage) {
            showToast("Medicine and dosage are required!", "error");
            return;
        }

        try {
            const response = await fetch(`${baseUrl}/api/prescriptions/create/`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    patient: currentPatientId,
                    doctor: doctorId,
                    medicine: medicine,
                    dosage: dosage,
                    notes: notes
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || "Failed to submit prescription");
            }

            showToast("Prescription submitted successfully!", "success");
            prescriptionForm.reset();
            prescriptionFormContainer.classList.add("hidden");
            
        } catch (error) {
            console.error("Error submitting prescription:", error);
            showToast(error.message || "Failed to submit prescription", "error");
        }
    }

    // Handle Medical Report Submission
    async function handleMedicalReportSubmit(e) {
        e.preventDefault();

        const diagnosis = document.getElementById("diagnosis").value;
        const treatment = document.getElementById("treatment").value;
        const notes = document.getElementById("notes").value;
        const fileInput = document.getElementById("report-file").files[0];
        
        const formData = new FormData();
        formData.append("patient", currentPatientId);
        formData.append("doctor", doctorId);
        formData.append("diagnosis", diagnosis);
        formData.append("treatment_plan", treatment);
        formData.append("notes", notes);
        if (fileInput) formData.append("report_file", fileInput);

        try {
            const response = await fetch(`${baseUrl}/api/prescriptions/medical-report/create/`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` },
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || "Failed to submit medical report");
            }

            showToast("Medical report submitted successfully!", "success");
            reportForm.reset();
            reportModal.classList.add("hidden");
            
        } catch (error) {
            console.error("Error submitting medical report:", error);
            showToast(error.message || "Failed to submit medical report", "error");
        }
    }

    // Fetch Appointments
    async function fetchAppointments() {
        if (!currentPatientId) return;

        try {
            const response = await fetch(`${baseUrl}/api/appointments/patient/${currentPatientId}/appointments/`, {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            });

            if (!response.ok) throw new Error("Failed to fetch appointments");

            const data = await response.json();
            renderAppointments(Array.isArray(data) ? data : [data]);
            
        } catch (error) {
            console.error("Error fetching appointments:", error);
            showToast("Failed to load appointments", "error");
        }
    }

    function renderAppointments(appointments) {
        if (!appointmentsList) return;
        
        appointmentsList.innerHTML = appointments.length === 0
            ? "<p class='text-gray-600'>No appointments found for this patient.</p>"
            : appointments.map(appointment => `
                <div class="bg-white p-6 rounded-lg shadow-md">
                    <div class="flex justify-between items-center">
                        <div>
                            <h3 class="text-xl font-semibold">Appointment #${appointment.id}</h3>
                            <p class="text-gray-600">${new Date(appointment.date).toLocaleDateString()} at ${appointment.time}</p>
                        </div>
                        <span class="px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(appointment.status)}">
                            ${appointment.status}
                        </span>
                    </div>
                    <div class="mt-4">
                        <p class="text-gray-700"><span class="font-semibold">Reason:</span> ${appointment.reason || 'N/A'}</p>
                    </div>
                </div>
            `).join("");
    }

    function getStatusColor(status) {
        if (!status) return "bg-gray-100 text-gray-800";
        switch (status.toLowerCase()) {
            case "pending": return "bg-yellow-100 text-yellow-800";
            case "completed": return "bg-green-100 text-green-800";
            case "cancelled": return "bg-red-100 text-red-800";
            default: return "bg-gray-100 text-gray-800";
        }
    }

    // Show Toast Notification
    function showToast(message, type = "success") {
        const toast = document.createElement("div");
        toast.className = `fixed bottom-4 right-4 px-4 py-2 rounded-md shadow-lg text-white ${
            type === "success" ? "bg-green-500" : "bg-red-500"
        }`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 3000);
    }

    // Setup Event Listeners
    function setupEventListeners() {
        // Profile View/Edit Toggle
        if (profileViewBtn && profileEditBtn) {
            profileViewBtn.addEventListener("click", () => {
                profileViewContent?.classList.remove("hidden");
                profileEditContent?.classList.add("hidden");
                profileViewBtn.classList.add("bg-blue-600", "text-white");
                profileEditBtn.classList.remove("bg-blue-600", "text-white");
            });

            profileEditBtn.addEventListener("click", () => {
                profileViewContent?.classList.add("hidden");
                profileEditContent?.classList.remove("hidden");
                profileEditBtn.classList.add("bg-blue-600", "text-white");
                profileViewBtn.classList.remove("bg-blue-600", "text-white");
            });
        }

        // Profile Picture Preview
        if (profilePicInput && profilePicPreview) {
            profilePicInput.addEventListener("change", function() {
                if (this.files?.[0]) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        profilePicPreview.src = e.target.result;
                        profilePicPreview.classList.remove("hidden");
                    };
                    reader.readAsDataURL(this.files[0]);
                }
            });
        }

        // Profile Form Submission
        if (profileForm) {
            profileForm.addEventListener("submit", handleProfileUpdate);
        }

        // Patient Search
        if (searchBar) {
            searchBar.addEventListener("input", (e) => {
                const searchTerm = e.target.value.toLowerCase();
                const patients = Array.from(patientsListElement?.children || []);
                
                patients.forEach(patient => {
                    const patientName = patient.querySelector(".font-semibold")?.innerText.toLowerCase() || "";
                    patient.classList.toggle("hidden", !patientName.includes(searchTerm));
                });
            });
        }

        // Close Patient Modal
        if (document.getElementById("close-modal")) {
            document.getElementById("close-modal").addEventListener("click", () => {
                document.getElementById("patient-modal")?.classList.add("hidden");
            });
        }

        // Prescription Form
        if (writePrescriptionBtn) {
            writePrescriptionBtn.addEventListener("click", () => {
                prescriptionFormContainer?.classList.toggle("hidden");
            });
        }
        if (prescriptionForm) {
            prescriptionForm.addEventListener("submit", handlePrescriptionSubmit);
        }

        // Medical Report Form
        if (writeReportBtn) {
            writeReportBtn.addEventListener("click", () => {
                reportModal?.classList.remove("hidden");
            });
        }
        if (closeModalBtn) {
            closeModalBtn.addEventListener("click", () => {
                reportModal?.classList.add("hidden");
            });
        }
        if (reportForm) {
            reportForm.addEventListener("submit", handleMedicalReportSubmit);
        }

        // View Appointments
        if (viewAppointmentsBtn) {
            viewAppointmentsBtn.addEventListener("click", fetchAppointments);
        }
    }
});