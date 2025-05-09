document.addEventListener('DOMContentLoaded', function() {
    // Auto focus on student ID input
    document.getElementById('student_id').focus();

    // Set default date to today
    document.getElementById('attendance_date').valueAsDate = new Date();

    // Form submission handler
    const form = document.getElementById('attendanceForm');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get the selected subject ID
        const subjectSelect = document.getElementById('subject');
        const subjectId = subjectSelect.value;
        
        if (!subjectId) {
            showError('Please select a subject');
            return;
        }
        
        // Check session date validity if we have session dates stored
        const sessionStartDate = document.getElementById('student_session_start_date')?.value;
        const sessionEndDate = document.getElementById('student_session_end_date')?.value;
        
        if (sessionStartDate && sessionEndDate) {
            const isDateValid = checkSessionDateValidity(sessionStartDate, sessionEndDate);
            if (!isDateValid) {
                showError('Cannot record attendance: Date is outside the student session period');
                return;
            }
        }
        
        // Set the subject_id in the hidden input
        document.getElementById('attendance_subject_id').value = subjectId;
        
        // Get form data
        const formData = new FormData(form);
        
        // Disable submit button and show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
        submitBtn.disabled = true;

        // Submit the form
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Handle success response
                if (data.was_updated) {
                    showSuccess(`${data.message} (Changed from ${data.old_status} to ${data.new_status})`);
                } else {
                    showSuccess(data.message);
                }
                
                // Clear form
                document.getElementById('student_id').value = '';
                document.getElementById('student_info').classList.remove('active');
                document.getElementById('attendance_details').style.display = 'none';
                document.getElementById('countdown_container').style.display = 'none';
                
                // Re-enable the student ID input field after successful submission
                document.getElementById('student_id').disabled = false;
                
                // Clear table data
                clearStudentTableData();
                
                // Refocus on the student ID input field for the next attendance
                document.getElementById('student_id').focus();
            } else if (data.status === 'duplicate') {
                // Handle duplicate attendance (student already registered)
                // Show modal with current status and options to update
                $('#duplicate_student_name').text(data.student_name);
                $('#duplicate_subject').text(data.subject);
                $('#duplicate_date').text(data.date);
                $('#duplicate_status').text(data.current_status);
                
                // Set the initial radio button based on current status
                if (data.current_status === 'Present') {
                    $('#update_status_present').prop('checked', true);
                } else {
                    $('#update_status_absent').prop('checked', true);
                }
                
                // Store student_id in the modal for the update
                $('#alreadyRegisteredModal').data('student_id', data.student_id);
                
                // Show the modal
                $('#alreadyRegisteredModal').modal('show');
            } else {
                // Handle error
                showError(data.message || 'An error occurred');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('An error occurred while processing your request.');
            // Enable student ID input field if lookup fails
            document.getElementById('student_id').disabled = false;
        })
        .finally(() => {
            // Reset button state
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        });
    });

    // Timer functionality
    let countdownInterval;
    let secondsLeft = 5; 
    
    // Function to start the countdown timer
    function startCountdownTimer() {
        // Reset timer and show the countdown container
        secondsLeft = 5; // Changed from 15 to 10 seconds
        document.getElementById('countdown_timer').textContent = secondsLeft;
        document.getElementById('countdown_container').style.display = 'block';
        
        // Clear any existing interval
        if (countdownInterval) {
            clearInterval(countdownInterval);
        }
        
        // Start the countdown
        countdownInterval = setInterval(function() {
            secondsLeft--;
            document.getElementById('countdown_timer').textContent = secondsLeft;
            
            if (secondsLeft <= 0) {
                // Clear the interval
                clearInterval(countdownInterval);
                
                // Submit the form automatically
                document.getElementById('attendance_button').click();
            }
        }, 1000);
    }
    
    // Function to stop the countdown timer
    function stopCountdownTimer() {
        if (countdownInterval) {
            clearInterval(countdownInterval);
            document.getElementById('countdown_container').style.display = 'none';
        }
    }
    
    // Decline button - Clears the student info and cancels the timer
    document.getElementById('btn_cancel_timer').addEventListener('click', function() {
        stopCountdownTimer();
        
        // Clear form
        document.getElementById('student_id').value = '';
        document.getElementById('student_id').disabled = false;  // Re-enable the input field
        document.getElementById('student_info').classList.remove('active');
        document.getElementById('attendance_details').style.display = 'none';
        
        // Clear table data
        clearStudentTableData();
        
        // Show declined message
        showWarning('Attendance registration declined.');
        
        // Refocus on the student ID input field
        document.getElementById('student_id').focus();
    });
    
    // Cancel auto-submit button - Just cancels the timer
    document.getElementById('btn_manual_submit').addEventListener('click', function() {
        stopCountdownTimer();
        showInfo('Auto-submit cancelled. You can manually submit when ready.');
    });

    // Function to show info message (blue)
    function showInfo(message) {
        const warningDiv = document.getElementById('warning_message');
        const warningText = document.getElementById('warning_text');
        warningText.textContent = message;
        warningDiv.style.display = 'block';
        warningDiv.classList.add('show');
        warningDiv.style.backgroundColor = '#17a2b8';  // Change to info color
        
        // Hide success and error messages if shown
        const successDiv = document.getElementById('success_message');
        successDiv.style.display = 'none';
        successDiv.classList.remove('show');
        
        const errorDiv = document.getElementById('error_message');
        errorDiv.style.display = 'none';
        errorDiv.classList.remove('show');
        
        // Auto hide after 5 seconds
        setTimeout(() => {
            warningDiv.style.display = 'none';
            warningDiv.classList.remove('show');
            warningDiv.style.backgroundColor = '';  // Reset to default
        }, 5000);
    }
});

// Clear student table data
function clearStudentTableData() {
    const tableFields = [
        'table_student_name', 'table_student_code', 'table_student_email',
        'table_student_gender', 'table_student_course', 'table_student_session',
        'table_student_session_years'
    ];
    
    tableFields.forEach(field => {
        document.getElementById(field).textContent = '-';
    });
}

function showError(message) {
    const errorDiv = document.getElementById('error_message');
    const errorText = document.getElementById('error_text');
    errorText.textContent = message;
    errorDiv.style.display = 'block';
    errorDiv.classList.add('show');
    
    // Hide success and warning messages if shown
    const successDiv = document.getElementById('success_message');
    successDiv.style.display = 'none';
    successDiv.classList.remove('show');
    
    const warningDiv = document.getElementById('warning_message');
    warningDiv.style.display = 'none';
    warningDiv.classList.remove('show');
    
    // Auto hide after 5 seconds
    setTimeout(() => {
        errorDiv.style.display = 'none';
        errorDiv.classList.remove('show');
    }, 5000);
}

function showWarning(message) {
    const warningDiv = document.getElementById('warning_message');
    const warningText = document.getElementById('warning_text');
    warningText.textContent = message;
    warningDiv.style.display = 'block';
    warningDiv.classList.add('show');
    
    // Hide success and error messages if shown
    const successDiv = document.getElementById('success_message');
    successDiv.style.display = 'none';
    successDiv.classList.remove('show');
    
    const errorDiv = document.getElementById('error_message');
    errorDiv.style.display = 'none';
    errorDiv.classList.remove('show');
    
    // Auto hide after 5 seconds
    setTimeout(() => {
        warningDiv.style.display = 'none';
        warningDiv.classList.remove('show');
    }, 5000);
}

function showSuccess(message) {
    const successDiv = document.getElementById('success_message');
    const successText = document.getElementById('success_text');
    successText.textContent = message;
    successDiv.style.display = 'block';
    successDiv.classList.add('show');
    
    // Hide warning and error messages if shown
    const warningDiv = document.getElementById('warning_message');
    warningDiv.style.display = 'none';
    warningDiv.classList.remove('show');
    
    const errorDiv = document.getElementById('error_message');
    errorDiv.style.display = 'none';
    errorDiv.classList.remove('show');
    
    // Auto hide after 5 seconds
    setTimeout(() => {
        successDiv.style.display = 'none';
        successDiv.classList.remove('show');
    }, 5000);
}

// Function to check if student's course is compatible with staff's course
function checkCourseCompatibility(studentCourse) {
    const staffCourse = document.getElementById('staff_course').value;
    const compatibilityIndicator = document.getElementById('course_compatibility');
    const attendanceButton = document.getElementById('attendance_button');
    
    // Compare courses
    if (studentCourse.toLowerCase() === staffCourse.toLowerCase()) {
        // Courses match
        compatibilityIndicator.textContent = "Student is registered with your course";
        compatibilityIndicator.className = "course-compatibility course-compatible";
        
        // Enable attendance button
        attendanceButton.disabled = false;
        
        // Show success notification
        showSuccess("Student is already registered with you. You can record their attendance.");
        
        return true;
    } else {
        // Courses don't match
        compatibilityIndicator.textContent = "The student is registered in " + studentCourse + " course and not registered in " + staffCourse;
        compatibilityIndicator.className = "course-compatibility course-incompatible";
        
        // Disable attendance button
        attendanceButton.disabled = true;
        
        // Show warning notification
        showWarning("This student cannot be registered due to course mismatch.");
        
        return false;
    }
}

// Function to verify the attendance date is within the session period
function checkSessionDateValidity(sessionStartDate, sessionEndDate) {
    const attendanceDate = document.getElementById('attendance_date').value;
    const sessionStartDateObj = new Date(sessionStartDate);
    const sessionEndDateObj = new Date(sessionEndDate);
    const attendanceDateObj = new Date(attendanceDate);
    
    // Create container for date validation message if it doesn't exist
    if (!document.getElementById('date_validity_container')) {
        const dateValidityContainer = document.createElement('div');
        dateValidityContainer.id = 'date_validity_container';
        dateValidityContainer.className = 'date-validity-container';
        
        // Get the attendance details container
        const attendanceDetails = document.getElementById('attendance_details');
        
        // Create a wrapping container for the date validator to ensure proper placement
        const validatorWrapper = document.createElement('div');
        validatorWrapper.className = 'form-group date-validator-wrapper';
        validatorWrapper.appendChild(dateValidityContainer);
        
        // Simply append it to the attendance details container
        attendanceDetails.appendChild(validatorWrapper);
        
        // Add CSS for the date validation display
        const style = document.createElement('style');
        style.textContent = `
            .date-validator-wrapper {
                margin-top: 10px;
                margin-bottom: 15px;
                order: 3;
            }
            .date-validity-container {
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 14px;
            }
            
            .date-valid {
                background-color: rgba(40, 167, 69, 0.15);
                color: #28a745;
                border: 1px solid rgba(40, 167, 69, 0.3);
            }
            
            .date-invalid {
                background-color: rgba(220, 53, 69, 0.15);
                color: #dc3545;
                border: 1px solid rgba(220, 53, 69, 0.3);
            }
        `;
        document.head.appendChild(style);
    }
    
    const dateValidityContainer = document.getElementById('date_validity_container');
    const attendanceButton = document.getElementById('attendance_button');
    
    // Check if the attendance date is within the session period
    if (attendanceDateObj >= sessionStartDateObj && attendanceDateObj <= sessionEndDateObj) {
        dateValidityContainer.textContent = "✓ Attendance date is within the session period";
        dateValidityContainer.className = "date-validity-container date-valid";
        attendanceButton.disabled = false;
        return true;
    } else {
        const formattedStartDate = sessionStartDate.split('-').reverse().join('/');
        const formattedEndDate = sessionEndDate.split('-').reverse().join('/');
        
        dateValidityContainer.textContent = `⚠ Attendance date must be within session period (${formattedStartDate} - ${formattedEndDate})`;
        dateValidityContainer.className = "date-validity-container date-invalid";
        attendanceButton.disabled = true;
        
        // Show warning notification
        showWarning("Attendance date is outside the student's session period.");
        return false;
    }
}

// Set first letter of name for photo placeholder
function setPhotoPlaceholder(name) {
    if (!name) return;
    
    const placeholder = document.getElementById('student_photo_placeholder');
    const firstLetter = name.trim().charAt(0).toUpperCase();
    placeholder.innerHTML = firstLetter;
}

// Handle student lookup - FIXED VERSION
let typingTimer;
const doneTypingInterval = 500; // wait for 500ms after user stops typing

document.addEventListener('DOMContentLoaded', function() {
    const studentIdInput = document.getElementById('student_id');
    if (studentIdInput) {
        studentIdInput.addEventListener('input', function() {
            clearTimeout(typingTimer);
            let studentId = this.value;
            
            // Try to parse JSON if the input looks like JSON data from QR code
            if (studentId.trim().startsWith('{') && studentId.trim().endsWith('}')) {
                try {
                    const jsonData = JSON.parse(studentId);
                    if (jsonData.student_code) {
                        // Extract just the student code from the JSON
                        studentId = jsonData.student_code;
                        // Update the input field to show only the student code
                        this.value = studentId;
                        
                        // Also update the hidden field
                        document.getElementById('attendance_student_id').value = studentId;
                        
                        console.log("Extracted student_code from QR JSON:", studentId);
                    }
                } catch (e) {
                    console.error("Failed to parse QR JSON data:", e);
                    // Continue with the raw input if JSON parsing fails
                }
            }
            
            // Hide student info and attendance details when input is empty
            if (!studentId) {
                document.getElementById('student_info').classList.remove('active');
                document.getElementById('attendance_details').style.display = 'none';
                document.getElementById('countdown_container').style.display = 'none';
                stopCountdownTimer(); // Stop the timer if it's running
                return;
            }
            
            // Set the extracted student ID to the hidden field regardless
            document.getElementById('attendance_student_id').value = studentId;

            // Wait for user to stop typing before making the request
            typingTimer = setTimeout(() => {
                // Show loading state
                document.getElementById('student_info').classList.remove('active');
                document.getElementById('attendance_details').style.display = 'none';
                document.getElementById('countdown_container').style.display = 'none';
                
                // Get the CSRF token from the meta tag or a hidden input field
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                
                fetch(document.getElementById('studentInfoUrl').value, {
                    method: 'POST',
                    body: new URLSearchParams({
                        'student_id': studentId,
                        'csrfmiddlewaretoken': csrfToken
                    }),
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                })
                .then(response => {
                    console.log('Response status:', response.status); // Debug log
                    if (!response.ok) {
                        return response.json().then(data => {
                            throw new Error(data.error || 'Network response was not ok');
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Received data:', data); // Debug log
                    if (data.error) {
                        showError(data.error);
                        return;
                    }

                    // Show student info and attendance details only if we have valid data
                    if (data.name && data.session) {
                        // Disable the student ID input field when a valid student is found
                        document.getElementById('student_id').disabled = true;
                        
                        // Update both the hidden fields (for form submission) and table display
                        
                        // Hidden fields
                        document.getElementById('student_name').value = data.name;
                        document.getElementById('student_email').value = data.email || 'Not provided';
                        document.getElementById('student_gender').value = data.gender || 'Not specified';
                        document.getElementById('display_student_code').value = data.student_code || 'Not assigned';
                        document.getElementById('student_session').value = data.session;
                        document.getElementById('student_session_years').value = data.session_years || 'Not specified';
                        document.getElementById('student_course').value = data.course || 'Not specified';
                        
                        // Store session dates in hidden fields for validation
                        if (!document.getElementById('student_session_start_date')) {
                            const startDateInput = document.createElement('input');
                            startDateInput.type = 'hidden';
                            startDateInput.id = 'student_session_start_date';
                            startDateInput.name = 'student_session_start_date';
                            document.getElementById('attendanceForm').appendChild(startDateInput);
                            
                            const endDateInput = document.createElement('input');
                            endDateInput.type = 'hidden';
                            endDateInput.id = 'student_session_end_date';
                            endDateInput.name = 'student_session_end_date';
                            document.getElementById('attendanceForm').appendChild(endDateInput);
                        }
                        
                        // Set session date values
                        if (data.session_start_date && data.session_end_date) {
                            document.getElementById('student_session_start_date').value = data.session_start_date;
                            document.getElementById('student_session_end_date').value = data.session_end_date;
                        }
                        
                        // Table display fields
                        document.getElementById('table_student_name').textContent = data.name;
                        document.getElementById('table_student_code').textContent = data.student_code || 'Not assigned';
                        document.getElementById('table_student_email').textContent = data.email || 'Not provided';
                        document.getElementById('table_student_gender').textContent = data.gender || 'Not specified';
                        document.getElementById('table_student_session').textContent = data.session;
                        document.getElementById('table_student_session_years').textContent = data.session_years || 'Not specified';
                        document.getElementById('table_student_course').textContent = data.course || 'Not specified';
                        
                        // Set profile photo if available
                        const photoPlaceholder = document.getElementById('student_photo_placeholder');
                        const photoImage = document.getElementById('student_photo');
                        
                        if (data.profile_pic) {
                            // Check if the path already starts with a slash
                            if (data.profile_pic.startsWith('/')) {
                                photoImage.src = data.profile_pic;
                            } else if (data.profile_pic.startsWith('media/')) {
                                // Add the leading slash if it starts with 'media/'
                                photoImage.src = '/' + data.profile_pic;
                            } else {
                                // Otherwise assume it needs the full /media/ prefix
                                photoImage.src = '/media/' + data.profile_pic;
                            }
                            photoImage.style.display = 'block';
                            photoPlaceholder.style.display = 'none';
                        } else {
                            photoImage.style.display = 'none';
                            photoPlaceholder.style.display = 'flex';
                            // Set the placeholder with first letter of name
                            setPhotoPlaceholder(data.name);
                        }
                        
                        // Check course compatibility
                        if (data.course) {
                            const isCompatible = checkCourseCompatibility(data.course);
                            
                            // Show attendance details only if courses are compatible
                            document.getElementById('attendance_details').style.display = isCompatible ? 'block' : 'none';
                            
                            // If course is compatible, check session date validity
                            if (isCompatible && data.session_start_date && data.session_end_date) {
                                const isDateValid = checkSessionDateValidity(data.session_start_date, data.session_end_date);
                                
                                // Add change event listener to the date field to revalidate when changed
                                document.getElementById('attendance_date').addEventListener('change', function() {
                                    checkSessionDateValidity(data.session_start_date, data.session_end_date);
                                });
                                
                                // Auto-select registered subjects if available
                                if (data.registered_subjects && data.registered_subjects.length > 0) {
                                    const subjectSelect = document.getElementById('subject');
                                    
                                    // If there's only one subject, select it automatically
                                    if (data.registered_subjects.length === 1) {
                                        const subjectId = data.registered_subjects[0].id;
                                        
                                        // Find and select the option with this value
                                        for (let i = 0; i < subjectSelect.options.length; i++) {
                                            if (subjectSelect.options[i].value == subjectId) {
                                                subjectSelect.selectedIndex = i;
                                                
                                                // Also set the hidden subject_id for form submission
                                                document.getElementById('attendance_subject_id').value = subjectId;
                                                
                                                // If we only have one subject, we can hide the dropdown
                                                // and show a simple text display instead
                                                const subjectContainer = subjectSelect.parentElement;
                                                const subjectLabel = subjectContainer.querySelector('label');
                                                
                                                // Create a div to show the selected subject
                                                const subjectDisplay = document.createElement('div');
                                                subjectDisplay.className = 'form-control-static';
                                                subjectDisplay.style.padding = '7px 0';
                                                subjectDisplay.style.fontWeight = '500';
                                                subjectDisplay.innerHTML = `${data.registered_subjects[0].name} <small class="text-success">(automatically selected)</small>`;
                                                
                                                // Hide the select and show the static text
                                                subjectSelect.style.display = 'none';
                                                subjectContainer.insertBefore(subjectDisplay, subjectSelect.nextSibling);
                                                
                                                // Start the countdown timer if date is valid and subject is selected
                                                if (isDateValid) {
                                                    startCountdownTimer();
                                                }
                                                
                                                break;
                                            }
                                        }
                                    } else if (data.registered_subjects.length > 1) {
                                        // If there are multiple subjects, filter the dropdown to only show registered ones
                                        const validSubjectIds = data.registered_subjects.map(subject => subject.id);
                                        
                                        // Create a note about registered subjects
                                        const noteElement = document.createElement('small');
                                        noteElement.className = 'form-text text-info';
                                        noteElement.textContent = 'Only showing subjects this student is registered for';
                                        subjectSelect.parentElement.appendChild(noteElement);
                                        
                                        // Hide options that aren't in the registered subjects
                                        for (let i = 0; i < subjectSelect.options.length; i++) {
                                            const option = subjectSelect.options[i];
                                            if (option.value && !validSubjectIds.includes(parseInt(option.value))) {
                                                option.style.display = 'none';
                                            }
                                        }
                                        
                                        // Add change event listener to the subject select
                                        subjectSelect.addEventListener('change', function() {
                                            if (this.value && isDateValid) {
                                                startCountdownTimer();
                                            }
                                        });
                                    }
                                }
                            }
                        } else {
                            // Can't determine compatibility without course
                            showWarning("Student course not specified. Cannot verify compatibility.");
                            document.getElementById('attendance_details').style.display = 'none';
                            document.getElementById('countdown_container').style.display = 'none';
                            
                            // Disable attendance button
                            document.getElementById('attendance_button').disabled = true;
                        }
                        
                        // Set QR code if available
                        const qrCodeContainer = document.getElementById('qr_code_container');
                        const qrCodeImage = document.getElementById('qr_code_image');
                        const studentCodeElement = document.getElementById('student_code');
                        
                        if (data.qr_code) {
                            qrCodeImage.src = '/media/' + data.qr_code;
                            qrCodeImage.style.display = 'block';
                            qrCodeContainer.style.display = 'block';
                        } else {
                            qrCodeImage.style.display = 'none';
                        }
                        
                        // Set student code if available
                        if (data.student_code) {
                            studentCodeElement.textContent = 'ID: ' + data.student_code;
                            studentCodeElement.style.display = 'block';
                        } else {
                            studentCodeElement.style.display = 'none';
                        }
                        
                        // Show the student info section
                        document.getElementById('student_info').classList.add('active');
                    } else {
                        showError('Student data not found. Please check the ID and try again.');
                    }
                })
                .catch(error => {
                    console.error('Error:', error); // Debug log
                    showError(error.message || 'Error fetching student data. Please try again.');
                    // Enable student ID input field if lookup fails
                    document.getElementById('student_id').disabled = false;
                });
            }, doneTypingInterval);
        });
    }
});

// Function to stop the countdown timer (defined globally so it can be called from multiple places)
function stopCountdownTimer() {
    const countdownInterval = window._countdownInterval;
    if (countdownInterval) {
        clearInterval(countdownInterval);
        window._countdownInterval = null;
        document.getElementById('countdown_container').style.display = 'none';
    }
}

// Function to start the countdown timer (defined globally so it can be called from multiple places)
function startCountdownTimer() {
    // Reset timer and show the countdown container
    let secondsLeft = 5; 
    document.getElementById('countdown_timer').textContent = secondsLeft;
    document.getElementById('countdown_container').style.display = 'block';
    
    // Clear any existing interval
    stopCountdownTimer();
    
    // Start the countdown
    window._countdownInterval = setInterval(function() {
        secondsLeft--;
        document.getElementById('countdown_timer').textContent = secondsLeft;
        
        if (secondsLeft <= 0) {
            // Clear the interval
            clearInterval(window._countdownInterval);
            window._countdownInterval = null;
            
            // Submit the form automatically
            document.getElementById('attendance_button').click();
        }
    }, 1000);
}