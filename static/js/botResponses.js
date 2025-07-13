// Comprehensive botResponses.js
export const responses = {
  // === Greetings ===
  'hello': 'Hello! I\'m your telehealth assistant. How can I help you today?',
  'hi': 'Hi there! I\'m here to help with your health questions. What\'s concerning you?',
  'hey': 'Hey! How are you feeling today?',
  'good morning': 'Good morning! Ready to support your health today. What do you need?',
  'good afternoon': 'Good afternoon! How can I assist with your health concerns?',
  'good evening': 'Good evening! Are you having any health issues I can help with?',

  // === Appointments ===
  'appointment': 'You can book appointments through our portal. Would you like me to guide you?',
  'need doctor': 'I can help connect you with a healthcare provider. Is this urgent or routine?',
  'book doctor': 'Let me help schedule your visit. Preferred type: video call or in-person?',
  'reschedule': 'To reschedule, please visit the appointments section or call our office.',
  'cancel appointment': 'You can cancel appointments through the patient portal. Need help?',

  // === Common Symptoms ===
  'headache': 'For headaches: rest in a quiet space, hydrate, and try a cool compress. If severe or with vision changes, seek care.',
  'migraine': 'For migraines: rest in a dark room, apply cold packs, and avoid triggers. Consider keeping a migraine diary.',
  'fever': 'For fever: rest, hydrate, and monitor temperature. If >102°F for >3 days or with rash, see a doctor.',
  'cough': 'For coughs: try warm fluids and honey. If with fever >100.4°F or lasting >3 weeks, get evaluated.',
  'sore throat': 'For sore throat: gargle warm salt water, stay hydrated. If with fever or white patches, see a doctor.',
  'runny nose': 'For runny nose: try saline spray, stay hydrated. If lasting >10 days or with colored mucus, get checked.',
  'congestion': 'For congestion: use steam inhalation, elevate your head at night. If with facial pain, consider sinus infection.',
  'nausea': 'For nausea: sip clear fluids, try ginger, and avoid strong smells. If with severe pain or vomiting, seek care.',
  'vomiting': 'For vomiting: start with small sips of clear fluids. If persistent >24hrs or with dehydration signs, get help.',
  'diarrhea': 'For diarrhea: follow BRAT diet (bananas, rice, applesauce, toast), hydrate well. If bloody or >3 days, see doctor.',
  'constipation': 'For constipation: increase fiber, water, and movement. If severe pain or >3 days without bowel movement, seek care.',
  'dizziness': 'For dizziness: sit down immediately to prevent falls. If with chest pain or weakness, call for help.',
  'fatigue': 'For fatigue: ensure quality sleep, balanced diet, and hydration. If persistent or with other symptoms, get evaluated.',
  'back pain': 'For back pain: try gentle stretches, heat/ice therapy. If with leg weakness or bladder changes, seek immediate care.',
  'joint pain': 'For joint pain: rest, ice, and OTC anti-inflammatories. If swollen, red, or warm to touch, see your doctor.',
  'rash': 'For rashes: avoid scratching, use cool compresses. If widespread, with fever, or painful, get medical attention.',
  'allergies': 'For allergies: avoid triggers, try antihistamines. If trouble breathing or swelling occurs, seek emergency care.',

  // === Mental Health ===
  'stress': 'Stress relief: try box breathing (4-4-4 counts), progressive muscle relaxation, or a short walk.',
  'anxious': 'Anxiety help: practice grounding techniques or the 5-4-3-2-1 method (identify things around you).',
  'overwhelmed': 'When overwhelmed: prioritize tasks, take breaks, and consider talking to someone you trust.',
  'depressed': 'For low mood: maintain routines, connect with loved ones. If persistent >2 weeks, consider professional help.',
  'panic': 'During panic: focus on slow breathing, remind yourself it will pass. If frequent, cognitive therapy can help.',
  'insomnia': 'For sleep troubles: keep consistent bedtime, limit screens before bed, avoid caffeine after noon.',

  // === Chronic Conditions ===
  'diabetes': 'Diabetes care: monitor blood sugar regularly, stay hydrated, watch for extreme highs/lows. Always carry fast-acting sugar.',
  'high blood pressure': 'For hypertension: limit salt, exercise regularly, take medications as prescribed. Monitor at home if possible.',
  'asthma': 'Asthma management: avoid triggers, use inhaler as directed. Seek help if rescue inhaler needed >2x/week or breathing worsens.',
  'allergy': 'Allergy care: avoid known triggers, keep medications handy. For severe reactions, always carry epinephrine.',

  // === Emergency ===
  'chest pain': '🚨 EMERGENCY: Chest pain with pressure, sweating, or nausea could be serious. Call 911 immediately.',
  'can\'t breathe': '🚨 EMERGENCY: Severe difficulty breathing requires immediate help. Call emergency services now.',
  'stroke symptoms': '🚨 EMERGENCY: Remember FAST (Face drooping, Arm weakness, Speech difficulty, Time to call)',
  'severe bleeding': '🚨 EMERGENCY: Apply direct pressure to wound. If bleeding doesn\'t stop in 10 mins, call 911.',
  'broken bone': '🚨 For suspected fractures: immobilize the area, apply ice, and seek emergency care.',
  'burn': 'For minor burns: cool with running water. For large burns or on face/hands, seek emergency care.',
  'poisoning': '🚨 If poisoning suspected: call Poison Control immediately at 1-800-222-1222.',

  // === Wellness & Prevention ===
  'sleep': 'Better sleep tips: keep consistent schedule, dark/cool room, limit caffeine after noon, wind down routine.',
  'diet': 'Healthy eating: focus on whole foods, colorful vegetables, lean proteins, whole grains, and stay hydrated.',
  'exercise': 'Movement matters: aim for 150 mins weekly of moderate activity. Find activities you enjoy for consistency.',
  'hydration': 'Hydration help: aim for 8 glasses daily, more if active. Pale yellow urine indicates good hydration.',
  'weight loss': 'Healthy weight loss: focus on sustainable changes - balanced diet, regular activity, and adequate sleep.',
  'immunization': 'Vaccines help prevent serious illnesses. Check with your doctor about recommended immunizations.',
  'checkup': 'Regular checkups help catch issues early. Adults should have annual physicals, more often with chronic conditions.',

  // === Women's Health ===
  'pregnancy': 'Prenatal care is crucial. Take prenatal vitamins, avoid alcohol/smoking, and attend all OB appointments.',
  'menstrual': 'For menstrual pain: try heat, gentle exercise, OTC pain relievers. If severe or disrupting life, see your GYN.',
  'menopause': 'Menopause management: dress in layers, limit triggers, consider discussing symptoms with your doctor.',

  // === Pediatric ===
  'baby fever': 'For infants <3mo with fever >100.4°F: seek immediate care. For older babies, monitor and call if >102°F.',
  'teething': 'For teething: try chilled teethers, gentle gum massage. Avoid numbing gels due to safety concerns.',
  'vaccine schedule': 'Vaccines protect children from serious diseases. Follow CDC recommended schedule for best protection.',

  // === Senior Health ===
  'memory': 'For memory concerns: establish routines, use reminders. If interfering with daily life, discuss with doctor.',
  'balance': 'Fall prevention: remove home hazards, do balance exercises, have vision checked annually.',
  'arthritis': 'Arthritis care: gentle movement helps, apply heat/cold as needed, maintain healthy weight to reduce joint stress.',

  // === COVID/FLU ===
  'covid': 'COVID symptoms: isolate if positive, rest/hydrate. Seek care if trouble breathing or oxygen levels drop below 92%.',
  'flu': 'Flu care: rest, fluids, OTC meds for symptoms. High-risk patients should contact doctor about antivirals.',
  // === Appointments ===
  'appointment': 'You can book appointments through our portal. Would you like to:\n1. Book a new appointment\n2. Check existing appointments\n3. Reschedule an appointment\nPlease reply with the number of your choice.',
  'need doctor': 'I can help you find available doctors. Please specify:\n- Preferred specialty (if any)\n- Urgency (urgent/routine)\n- Preferred appointment type (video/in-person)',
  'book doctor': 'Let\'s schedule your visit. First, please specify:\n1. Doctor\'s name/specialty\n2. Preferred date range\n3. Video or in-person visit',
  'reschedule': 'To reschedule, I\'ll need:\n1. Your appointment ID\n2. New preferred date/time\n3. Reason for rescheduling\nWould you like to proceed?',
  'cancel appointment': 'To cancel an appointment, I need:\n1. Appointment ID\n2. Reason for cancellation\nNote: Cancellations within 24 hours may incur fees.',

  // === Appointment Status ===
  'appointment status': 'To check your appointment status, I\'ll need:\n1. Your patient ID\n2. Appointment date\nWould you like me to look this up for you?',
  'confirm appointment': 'Appointment confirmations are sent via email/SMS. I can verify - please provide:\n1. Doctor\'s name\n2. Scheduled date',
  'upcoming appointments': 'To view upcoming appointments, I can check your schedule. Please verify your patient ID.',

  // === Doctor Information ===
  'doctor availability': 'Doctor availability varies. Please specify:\n- Doctor\'s name\n- Date range\n- Morning/afternoon preference\nI\'ll check real-time availability.',
  'doctor contact': 'For doctor contact information, I need to know:\n1. Doctor\'s name\n2. Your relationship (current patient/new patient)',
  'doctor specialty': 'Our specialists include:\n- Cardiologists\n- Dermatologists\n- Pediatricians\n- General Practitioners\nWhich specialty do you need?',

  // === Billing/Payment ===
  'payment': 'For billing questions, I can help with:\n1. Appointment fees\n2. Payment methods\n3. Insurance queries\nWhat do you need to know?',
  'appointment cost': 'Consultation fees vary by doctor and visit type:\n- Video visit: $50-$100\n- In-person: $75-$150\n- Specialist: $100-$300\nNeed a specific quote?',
  'insurance': 'We accept most major insurers. To verify coverage:\n1. Provide insurer name\n2. Member ID\n3. Doctor/service needed\nShall I check for you?',

  // === Hospital Information ===
  'hospital': 'Our hospital locations include:\n1. Main Campus (Downtown)\n2. Westside Medical Center\n3. Northside Clinic\nWhich location are you interested in?',
  'hospital hours': 'General hospital hours:\n- Weekdays: 7am-9pm\n- Weekends: 8am-5pm\nEmergency: 24/7\nNeed specific department hours?',
  'hospital contact': 'Main hospital contact:\n📞 (254) 123-4567\n📧 info@telehealth.com\n📍 123 Medical Center Dr\nNeed a specific department?',
  // === Default ===
  'default': 'I want to understand your concern better. Could you describe more about what you\'re experiencing? If this is urgent, please say "emergency".'
};