document.addEventListener("DOMContentLoaded", function () {
  const baseUrl = window.location.origin;
  const token = localStorage.getItem("access_token");

  async function getDoctorProfile() {
    try {
      const response = await fetch(`${baseUrl}/api/users/doctor/profile/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        throw new Error('Failed to fetch doctor data');
      }
    } catch (error) {
      console.error(error);
    }
  }

  async function getDoctorPatients() {
    try {
      const res = await fetch(`${baseUrl}/api/users/doctor/patient/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (res.ok) {
        const doctorpatients = await res.json();
        return doctorpatients;
      } else {
        throw new Error('Failed to fetch patient data');
      }
    } catch (error) {
      console.error(error);
    }
  }

  async function DoctorMessaging() {
    // Placeholder for future messaging logic
  }
});
