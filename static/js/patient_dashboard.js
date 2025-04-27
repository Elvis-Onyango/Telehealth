// DOM Elements - Organized in a single object for better management
import { responses } from './botResponses.js';

const baseUrl = window.location.origin;
const token = localStorage.getItem('access_token');
const elements = {
  darkModeToggle: document.getElementById('darkModeToggle'),
  body: document.getElementById('body'),
  notificationButton: document.getElementById('notificationButton'),
  notificationCount: document.getElementById('notificationCount'),
  searchInput: document.getElementById('search-input'),
  profileCardsContainer: document.getElementById('profile-cards'),
  profilePictureNav: document.getElementById('profile-picture-nav'),
  profileName: document.getElementById('profile-name'),
  chatbotMessages: document.getElementById('chatbot-messages'),
  chatbotInputField: document.getElementById('chatbot-input-field'),
  calendarEl: document.getElementById('calendar'),
  communicationBtn: document.querySelector("[data-action='communication']")
};

// Theme Manager - Encapsulates dark mode functionality
const themeManager = {
  init() {
    this.loadThemePreference();
    elements.darkModeToggle.addEventListener('click', this.toggleTheme.bind(this));
  },
  
  toggleTheme() {
    elements.body.classList.toggle('dark-mode');
    elements.darkModeToggle.classList.toggle('active');
    localStorage.setItem('darkMode', elements.body.classList.contains('dark-mode'));
  },
  
  loadThemePreference() {
    if (localStorage.getItem('darkMode') === 'true') {
      elements.body.classList.add('dark-mode');
      elements.darkModeToggle.classList.add('active');
    }
  }
};

// Notification Handler
const notificationHandler = {
  init() {
    elements.notificationButton.addEventListener('click', this.handleNotificationClick);
  },
  
  handleNotificationClick() {
    alert('You have 3 new notifications!');
    elements.notificationCount.classList.add('hidden');
  }
};

// Search Handler
const searchHandler = {
  init() {
    elements.searchInput.addEventListener('input', this.handleSearchInput);
  },
  
  handleSearchInput() {
    const searchTerm = elements.searchInput.value.toLowerCase();
    console.log('Search term:', searchTerm);
    // Implement actual search logic here
  }
};

// Profile Data Handler
const profileHandler = {
  async fetchPatientProfile() {


    try {
      const response = await fetch(`${baseUrl}/api/users/patient/profile/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log(data)
        this.renderProfileCards(data);
        this.renderCharts(data);
        this.updateNavbarProfile(data);

      } else {
        throw new Error(`Failed to fetch patient profile. Status: ${response.status}`);
      }
    } catch (error) {
      console.error('Error fetching patient profile:', error);
      this.showErrorState();
    }
  },
  
  showErrorState() {
    elements.profileCardsContainer.innerHTML = `
      <div class="error-state bg-white dark:bg-gray-800 rounded-xl p-6 text-center">
        <span class="material-icons text-red-500 text-5xl mb-4">error</span>
        <h3 class="text-lg font-medium dark:text-white">Failed to load profile data</h3>
        <p class="text-gray-600 dark:text-gray-400 mt-2">Please try again later</p>
        <button class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          onclick="profileHandler.fetchPatientProfile()">
          Retry
        </button>
      </div>
    `;
  },
  
renderProfileCards(data) {
  const doctor = data.doctors?.length > 0 ? data.doctors[0] : { 
    first_name: 'No', 
    last_name: 'Doctor', 
    specialization: 'Not assigned',
    profile_picture: '/static/images/default-doctor.png'
  };


  const formatValue = (value, fallback = 'Not provided') => 
    value ? value : fallback;
  
  const formatDate = (dateString) => 
    dateString ? new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    }) : 'Not provided';

  elements.profileCardsContainer.innerHTML = this.generateProfileCardsHTML(data, doctor, formatValue, formatDate);
  this.addCardHoverEffects();
},

generateProfileCardsHTML(data, doctor, formatValue, formatDate) {
  return `
  <div class="profile-grid grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
    <!-- Personal Information Card -->
    <div class="profile-card hover:shadow-lg transition-all duration-200">
      <div class="card-header bg-gradient-to-r from-cyan-500 to-cyan-600 dark:from-cyan-700 dark:to-cyan-800 p-5 rounded-t-xl flex justify-between items-center">
        <h2 class="text-xl font-semibold text-white">Personal Information</h2>
        <span class="material-icons-round text-white bg-white/20 p-2 rounded-full">person</span>
      </div>
      <div class="card-body p-5 bg-white dark:bg-gray-800 rounded-b-xl">
        <div class="space-y-4">
          ${this.generateProfileField('Full Name', `${formatValue(data.user?.first_name)} ${formatValue(data.user?.last_name)}`, 'user')}
          ${this.generateProfileField('Date of Birth', formatDate(data.date_of_birth), 'cake')}
          ${this.generateProfileField('Gender', formatValue(data.gender), 'other')}
          ${this.generateProfileField('Blood Type', formatValue(data.blood_type), 'bloodtype')}
        </div>
      </div>
    </div>

    <!-- Contact Information Card -->
    <div class="profile-card hover:shadow-lg transition-all duration-200">
      <div class="card-header bg-gradient-to-r from-blue-500 to-blue-600 dark:from-blue-700 dark:to-blue-800 p-5 rounded-t-xl flex justify-between items-center">
        <h2 class="text-xl font-semibold text-white">Contact Information</h2>
        <span class="material-icons-round text-white bg-white/20 p-2 rounded-full">contact_mail</span>
      </div>
      <div class="card-body p-5 bg-white dark:bg-gray-800 rounded-b-xl">
        <div class="space-y-4">
          ${this.generateProfileField('Email', formatValue(data.user?.email), 'email', true)}
          ${this.generateProfileField('Phone', formatValue(data.user?.phone), 'phone')}
          ${this.generateProfileField('Address', formatValue(data.user?.address), 'home')}
        </div>
      </div>
    </div>

    <!-- Medical Information Card -->
    <div class="profile-card hover:shadow-lg transition-all duration-200 lg:col-span-2 xl:col-span-1">
      <div class="card-header bg-gradient-to-r from-purple-500 to-purple-600 dark:from-purple-700 dark:to-purple-800 p-5 rounded-t-xl flex justify-between items-center">
        <h2 class="text-xl font-semibold text-white">Medical Information</h2>
        <span class="material-icons-round text-white bg-white/20 p-2 rounded-full">medical_services</span>
      </div>
      <div class="card-body p-5 bg-white dark:bg-gray-800 rounded-b-xl">
        <!-- Doctor Information Section -->
        <div class="mb-6">
          <h3 class="section-title flex items-center gap-2 text-lg font-medium text-gray-800 dark:text-white mb-3">
            <img src="${doctor.profile_picture}" alt="Doctor" class="w-10 h-10 rounded-full object-cover border-2 border-cyan-200">
            <span>Primary Physician</span>
          </h3>
          <div class="space-y-3 pl-12">
            ${this.generateProfileField('Name', `${doctor.first_name} ${doctor.last_name}`, 'badge')}
            ${this.generateProfileField('Specialization', doctor.specialization, 'medical_information')}
            <button class="mt-3 flex items-center gap-2 text-sm text-cyan-600 dark:text-cyan-400 hover:text-cyan-700 dark:hover:text-cyan-300 transition-colors">
              <span class="material-icons-round text-base">message</span>
              <span>Send Message</span>
            </button>
          </div>
        </div>
        
        <!-- Emergency Contact Section -->
        <div class="pt-4 border-t border-gray-200 dark:border-gray-700">
          <h3 class="section-title flex items-center gap-2 text-lg font-medium text-gray-800 dark:text-white mb-3">
            <span class="material-icons-round text-red-500">emergency</span>
            <span>Emergency Contact</span>
          </h3>
          <div class="space-y-3 pl-12">
            ${this.generateProfileField('Name', formatValue(data.emergency_contact_name), 'person')}
            ${this.generateProfileField('Phone', formatValue(data.emergency_contact_phone), 'call')}
            <button class="mt-3 flex items-center gap-2 text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors">
              <span class="material-icons-round text-base">add_alert</span>
              <span>Set Emergency Alert</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
  `;
},

generateProfileField(label, value, icon = null, breakAll = false) {
  return `
  <div class="flex items-start gap-3">
    ${icon ? `<span class="material-icons-round text-gray-500 dark:text-gray-400 mt-0.5">${icon}</span>` : ''}
    <div class="flex-1">
      <p class="field-label text-sm text-gray-500 dark:text-gray-400">${label}</p>
      <p class="field-value ${breakAll ? 'break-all' : ''} text-gray-800 dark:text-gray-100 font-medium">${value}</p>
    </div>
  </div>
  `;
},
  
  generateProfileField(label, value, breakAll = false) {
    return `
    <div>
      <p class="field-label">${label}</p>
      <p class="field-value ${breakAll ? 'break-all' : ''}">${value}</p>
    </div>
    `;
  },
  
  addCardHoverEffects() {
    const cards = elements.profileCardsContainer.querySelectorAll('.profile-card');
    cards.forEach(card => {
      card.style.transition = 'transform 0.2s ease, box-shadow 0.2s ease';
      
      card.addEventListener('mouseenter', () => {
        card.classList.add('hovered');
      });
      
      card.addEventListener('mouseleave', () => {
        card.classList.remove('hovered');
      });
    });
  },
  
  updateNavbarProfile(data) {
    if (data.user) {
      elements.profilePictureNav.src = data.profile_picture || 'default-profile.jpg';
      elements.profileName.textContent = `${data.user.first_name} ${data.user.last_name}`;
    }
  },
  
  renderCharts(data) {
    // Health Metrics Chart
    this.initChart('healthMetricsChart', {
      type: 'line',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
          label: 'Heart Rate',
          data: [72, 75, 70, 68, 74, 76],
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.3,
          fill: true,
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: true },
          tooltip: {
            mode: 'index',
            intersect: false,
          }
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false
        }
      }
    });

    // Medication History Chart
    this.initChart('medicationHistoryChart', {
      type: 'bar',
      data: {
        labels: ['Paracetamol', 'Ibuprofen', 'Amoxicillin', 'Vitamin C'],
        datasets: [{
          label: 'Medication Usage',
          data: [10, 5, 8, 12],
          backgroundColor: [
            'rgba(16, 185, 129, 0.7)',
            'rgba(59, 130, 246, 0.7)',
            'rgba(139, 92, 246, 0.7)',
            'rgba(245, 158, 11, 0.7)'
          ],
          borderColor: [
            'rgba(16, 185, 129, 1)',
            'rgba(59, 130, 246, 1)',
            'rgba(139, 92, 246, 1)',
            'rgba(245, 158, 11, 1)'
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
        },
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    });
  },
  
  initChart(elementId, config) {
    const ctx = document.getElementById(elementId)?.getContext('2d');
    if (ctx) {
      new Chart(ctx, config);
    }
  }
};

// Enhanced chatbotHandler.js
const chatbotHandler = {
  init() {
    elements.chatbotInputField.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.sendMessage();
      }
    });
  },

  sendMessage() {
    const message = elements.chatbotInputField.value.trim();
    if (!message) return;

    this.addMessage(message, 'user');
    this.simulateBotResponse(message);
    elements.chatbotInputField.value = '';
    this.scrollToBottom();
  },

  addMessage(content, sender) {
    const message = document.createElement('div');
    message.className = `message ${sender}`;
    message.innerHTML = `
      <div class="message-content">${content}</div>
      <div class="message-time">${this.getCurrentTime()}</div>
    `;
    elements.chatbotMessages.appendChild(message);
  },

  simulateBotResponse(message) {
    setTimeout(() => {
      const response = this.getEnhancedBotResponse(message);
      this.addMessage(response, 'bot');
      this.scrollToBottom();
    }, 500);
  },

  getEnhancedBotResponse(message) {
    if (typeof message !== 'string' || message.trim() === '') {
      return responses.default;
    }

    const lowerMessage = message.toLowerCase();

    // 1. Enhanced emergency detection with context
    const emergencyPatterns = [
      { 
        pattern: /(sharp|severe|crushing|radiating) chest pain/i, 
        response: responses['chest pain'] 
      },
      { 
        pattern: /(can'?t breathe|difficulty breathing|shortness of breath|choking)/i, 
        response: responses["can't breathe"] 
      },
      { 
        pattern: /(faint|passed out|lost consciousness|unresponsive)/i, 
        response: "🚨 This could be serious. Please seek immediate medical attention or call emergency services."
      }
    ];

    for (const { pattern, response } of emergencyPatterns) {
      if (pattern.test(lowerMessage)) {
        return response;
      }
    }

    // 2. Symptom severity assessment
    const severityKeywords = {
      mild: ['slight', 'mild', 'minor', 'a little'],
      moderate: ['moderate', 'some', 'annoying'],
      severe: ['severe', 'extreme', 'terrible', 'unbearable', 'worst']
    };

    // 3. Context-aware response scoring
    const keywordScores = {};
    const words = lowerMessage.split(/\s+/);

    Object.keys(responses).forEach(keyword => {
      if (keyword === 'default') return;

      // Exact match scoring
      if (lowerMessage.includes(keyword)) {
        keywordScores[keyword] = (keywordScores[keyword] || 0) + 5;

        // Position bonus (earlier mentions are more important)
        if (words.indexOf(keyword) < 5) {
          keywordScores[keyword] += 2;
        }

        // Severity adjustment
        for (const [severity, terms] of Object.entries(severityKeywords)) {
          if (terms.some(term => lowerMessage.includes(term))) {
            keywordScores[keyword] += severity === 'severe' ? 3 : 
                                     severity === 'moderate' ? 1 : 0;
            break;
          }
        }
      }

      // Partial/phrase matching
      const keywordParts = keyword.split(' ');
      if (keywordParts.length > 1) {
        const allPartsPresent = keywordParts.every(part => 
          lowerMessage.includes(part) || 
          this.findSimilarWords(part, words)
        );
        if (allPartsPresent) {
          keywordScores[keyword] = (keywordScores[keyword] || 0) + 3;
        }
      }
    });

    // 4. Determine best response
    let bestMatch = 'default';
    let highestScore = 0;

    for (const [keyword, score] of Object.entries(keywordScores)) {
      if (score > highestScore) {
        highestScore = score;
        bestMatch = keyword;
      }
    }

    // 5. Contextual follow-up system
    if (highestScore >= 3 && highestScore < 7) {
      const followUps = {
        'headache': this.getHeadacheFollowUp(lowerMessage),
        'fever': 'How long have you had the fever? Are you experiencing chills or sweating?',
        'stress': 'Would you like me to guide you through a quick relaxation exercise?',
        'cough': 'Is your cough dry or producing mucus? Any blood in the mucus?',
        'nausea': 'Are you experiencing vomiting or dizziness as well?',
        'pain': 'Can you describe the pain? (sharp, dull, throbbing, etc.)'
      };

      if (followUps[bestMatch]) {
        return followUps[bestMatch];
      }
    }

    // 6. Return the best matched response
    return responses[bestMatch] || responses.default;
  },

  // Helper methods
  findSimilarWords(target, wordList) {
    const synonymMap = {
      'hurt': ['pain', 'ache', 'sore', 'discomfort'],
      'headache': ['migraine', 'head pain', 'head pressure'],
      'fever': ['temperature', 'hot', 'burning up'],
      'tired': ['fatigue', 'exhausted', 'weary', 'drained'],
      'nausea': ['queasy', 'sick to stomach', 'want to vomit']
    };

    return synonymMap[target] 
      ? wordList.some(word => synonymMap[target].includes(word))
      : false;
  },

  getHeadacheFollowUp(message) {
    if (/(throbbing|pounding|pulsing)/i.test(message)) {
      return 'A throbbing headache could be a migraine. Are you sensitive to light or sound?';
    }
    if (/(pressure|tight)/i.test(message)) {
      return 'This might be a tension headache. Have you been stressed lately?';
    }
    return 'How long have you had this headache? Is it constant or comes and goes?';
  },

  getCurrentTime() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  },

  scrollToBottom() {
    elements.chatbotMessages.scrollTop = elements.chatbotMessages.scrollHeight;
  }
};


// Calendar Handler
const calendarHandler = {
  init() {
    if (elements.calendarEl) {
      this.calendar = new FullCalendar.Calendar(elements.calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
          left: 'prev,next today',
          center: 'title',
          right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: [
          { title: 'Appointment with Dr. Smith', date: new Date(), color: '#3b82f6' },
          { title: 'Follow-up with Dr. Johnson', date: this.addDays(new Date(), 3), color: '#10b981' },
        ],
        eventClick: (info) => {
          alert(`Event: ${info.event.title}\nDate: ${info.event.start.toLocaleDateString()}`);
        },
        eventContent: (arg) => {
          return {
            html: `
              <div class="fc-event-main">
                <span class="material-icons fc-event-icon">event</span>
                <span class="fc-event-title">${arg.event.title}</span>
              </div>
            `
          };
        }
      });
      this.calendar.render();
    }
  },
  
  addDays(date, days) {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
  }
};

// Communication Handler
const communicationHandler = {
  init() {
    if (!elements.communicationBtn) {
      console.error("Communication button not found.");
      return;
    }

    elements.communicationBtn.style.display = "flex";
    elements.communicationBtn.addEventListener("click", this.redirectToChat);
  },
  
  redirectToChat() {
    const baseUrl = window.location.origin;
    window.location.href = `${baseUrl}/api/messaging/chat/`;
  }
};

// Health Metrics Dashboard
const healthDashboard = {
  metrics: {
    steps: 7523,
    heartRate: 72,
    sleep: 6.5,
    hydration: 1.8,
    calories: 1200,
    activityLevel: 'Moderate',
    bloodPressure: '120/80',
    bloodOxygen: 98,
  },
  
  init() {
    this.updateMetrics();
    setInterval(() => this.simulateDataUpdate(), 5000);
  },
  
  
  
  updateMetrics() {
    Object.keys(this.metrics).forEach(key => {
      const element = document.getElementById(key);
      if (element) {
        if (key === 'bloodPressure') {
          element.textContent = `${this.metrics[key]} mmHg`;
        } else if (key === 'bloodOxygen') {
          element.textContent = `${this.metrics[key]}%`;
        } else if (key === 'heartRate') {
          element.textContent = `${this.metrics[key]} bpm`;
        } else if (key === 'hydration') {
          element.textContent = `${this.metrics[key]} L`;
        } else if (key === 'sleep') {
          element.textContent = `${this.metrics[key]} hrs`;
        } else if (key === 'calories') {
          element.textContent = `${this.metrics[key]} kcal`;
        } else {
          element.textContent = this.metrics[key];
        }
      }
    });
  },
  
  simulateDataUpdate() {
    this.metrics = {
      steps: this.metrics.steps + Math.floor(Math.random() * 500),
      heartRate: Math.floor(Math.random() * (80 - 60 + 1)) + 60,
      sleep: (6.5 + Math.random() * 1.5).toFixed(1),
      hydration: (1.8 + Math.random() * 0.5).toFixed(1),
      calories: this.metrics.calories + Math.floor(Math.random() * 100),
      activityLevel: ['Low', 'Moderate', 'High'][Math.floor(Math.random() * 3)],
      bloodPressure: `${Math.floor(Math.random() * (130 - 110 + 1)) + 110}/${Math.floor(Math.random() * (85 - 70 + 1)) + 70}`,
      bloodOxygen: Math.floor(Math.random() * (100 - 95 + 1)) + 95,
    };
    this.updateMetrics();
  }
};

// Reminder Handler
const reminderHandler = {
  init() {
    document.getElementById('add-reminder')?.addEventListener('click', this.addReminder);
  },
  
  addReminder() {
    const name = document.getElementById('medication-name').value.trim();
    const time = document.getElementById('medication-time').value;
    
    if (!name || !time) {
      alert('Please enter both medication name and time');
      return;
    }
    
    const reminder = document.createElement('li');
    reminder.className = 'reminder-item';
    reminder.innerHTML = `
      <span class="reminder-icon material-icons">notifications</span>
      <div class="reminder-content">
        <span class="reminder-name">${name}</span>
        <span class="reminder-time">${time}</span>
      </div>
      <button class="reminder-delete" onclick="reminderHandler.deleteReminder(this)">
        <span class="material-icons">delete</span>
      </button>
    `;
    
    document.getElementById('reminders').appendChild(reminder);
    this.clearInputs();
  },
  
  deleteReminder(button) {
    button.closest('.reminder-item').remove();
  },
  
  clearInputs() {
    document.getElementById('medication-name').value = '';
    document.getElementById('medication-time').value = '';
  }
};

// Navigation Handler
const navigationHandler = {
  init() {
    window.redirectToDoctorPage = this.redirectToDoctorPage;
  },
  
  redirectToDoctorPage() {
    const baseUrl = window.location.origin;
    window.location.href = `${baseUrl}/api/users/doctor-page`;
  }
};

// Medication Display Handler
const medicationDisplay = {
  init: function() {
    this.fetchMedications();
    document.getElementById('refreshMedsBtn')?.addEventListener('click', () => this.fetchMedications());
  },

  fetchMedications: async function() {
    const container = document.getElementById('medications-container');
    if (!container) {
      console.error('Medications container not found');
      return;
    }
    
    try {
      container.innerHTML = `
        <div class="flex justify-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      `;

      const response = await fetch(`${baseUrl}/api/prescriptions/create/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      
      const prescriptions = await response.json();
      this.displayMedications(prescriptions);
      
    } catch (error) {
      console.error('Medication fetch error:', error);
      container.innerHTML = `
        <div class="text-center py-6 text-danger text-sm">
          <span class="material-icons-round">error</span>
          <p>Could not load medications</p>
          <button onclick="medicationDisplay.fetchMedications()" class="mt-2 text-primary text-sm">
            Retry
          </button>
        </div>
      `;
    }
  },

  displayMedications: function(prescriptions) {
    const container = document.getElementById('medications-container');
    if (!container) return;

    if (!prescriptions || prescriptions.length === 0) {
      container.innerHTML = `
        <div class="text-center py-6 text-gray-500 dark:text-gray-400">
          <span class="material-icons-round">medication</span>
          <p>No active prescriptions found</p>
        </div>
      `;
      return;
    }

    container.innerHTML = prescriptions.map(prescription => {
      // Handle case where decrypted_prescription might be "Restricted Access"
      const medData = prescription.decrypted_prescription;
      
      if (medData === "Restricted Access") {
        return `
          <div class="medication-item border-b border-gray-100 dark:border-gray-700 py-4 last:border-0">
            <div class="flex gap-3 items-center text-gray-500 dark:text-gray-400">
              <span class="material-icons-round">lock</span>
              <div>
                <p class="font-medium">Encrypted Prescription</p>
                <p class="text-xs">Issued: ${new Date(prescription.date_issued).toLocaleDateString()}</p>
              </div>
            </div>
          </div>
        `;
      }

      // Parse the medication data if it's a JSON string
      let medication;
      try {
        medication = typeof medData === 'string' ? JSON.parse(medData) : medData;
      } catch (e) {
        console.error('Failed to parse medication data:', e);
        medication = {
          name: 'Unknown Medication',
          dosage: '--',
          frequency: '--',
          instructions: 'Contact your doctor for details'
        };
      }

      return `
        <div class="medication-item border-b border-gray-100 dark:border-gray-700 py-4 last:border-0">
          <div class="flex gap-3">
            <div class="bg-blue-100 text-blue-600 p-2 rounded-lg dark:bg-blue-900/30 dark:text-blue-200">
              <span class="material-icons-round">${this.getMedIcon(medication)}</span>
            </div>
            <div class="flex-1">
              <div class="flex justify-between">
                <h4 class="font-medium dark:text-white">${medication.name || 'Prescription'}</h4>
                <span class="text-xs text-gray-500 dark:text-gray-400">
                  ${new Date(prescription.date_issued).toLocaleDateString()}
                </span>
              </div>
              <div class="grid grid-cols-2 gap-2 mt-2 text-sm">
                <div>
                  <p class="text-gray-500 dark:text-gray-400">Dosage</p>
                  <p class="dark:text-white">${medication.dosage || '--'}</p>
                </div>
                <div>
                  <p class="text-gray-500 dark:text-gray-400">Frequency</p>
                  <p class="dark:text-white">${medication.frequency || '--'}</p>
                </div>
              </div>
              ${medication.instructions ? `
                <div class="mt-2 text-sm">
                  <p class="text-gray-500 dark:text-gray-400">Instructions</p>
                  <p class="dark:text-white">${medication.instructions}</p>
                </div>
              ` : ''}
              <div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
                Prescribed by: ${prescription.doctor_name || 'Unknown doctor'}
              </div>
            </div>
          </div>
        </div>
      `;
    }).join('');
  },

  getMedIcon: function(medication) {
    return medication.type === 'injection' ? 'vaccines' : 'medication';
  }
};

// Initialize all components when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  themeManager.init();
  notificationHandler.init();
  searchHandler.init();
  profileHandler.fetchPatientProfile();
  chatbotHandler.init();
  calendarHandler.init();
  communicationHandler.init();
  healthDashboard.init();
  reminderHandler.init();
  navigationHandler.init();
  medicationDisplay.init();

});

// Add global helper functions
window.enableCommunicationForPatients = communicationHandler.init.bind(communicationHandler);
window.goToConversations = () => {
  const baseUrl = window.location.origin;
  window.location.href = `${baseUrl}/messaging/conversations/`;
};



