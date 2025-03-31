import json
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt
from .models import Attendance, AttendanceReport, Student, Subject, Session
from .EmailBackend import EmailBackend
import logging
from datetime import datetime
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from .models import Student, AttendanceReport, LeaveReportStudent, FeedbackStudent, NotificationStudent
from django.contrib.auth.decorators import login_required

# Create your views here.

def login_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            return redirect(reverse("admin_home"))
        elif request.user.user_type == '2':
            return redirect(reverse("staff_home"))
        else:
            return redirect(reverse("student_home"))
    return render(request, 'main_app/login.html')


def doLogin(request, **kwargs):
    if request.method != 'POST':
        return HttpResponse("<h4>Denied</h4>")
    else:
        # Authenticate
        user = EmailBackend.authenticate(request, username=request.POST.get('email'), password=request.POST.get('password'))
        if user is not None:
            login(request, user)
            if user.user_type == '1':
                return redirect(reverse("admin_home"))
            elif user.user_type == '2':
                return redirect(reverse("staff_home"))
            else:
                return redirect(reverse("student_home"))
        else:
            messages.error(request, "Invalid details")
            return redirect("/")

def logout_user(request):
    if request.user is not None:
        logout(request)
    return redirect("/")



def delete_student(request, student_id):
    try:
        student = get_object_or_404(Student, id=student_id)
        user = student.admin

        # Delete related AttendanceReport records
        AttendanceReport.objects.filter(student=student).delete()

        # Delete related LeaveReportStudent records
        LeaveReportStudent.objects.filter(student=student).delete()

        # Delete related FeedbackStudent records
        FeedbackStudent.objects.filter(student=student).delete()

        # Delete related NotificationStudent records
        NotificationStudent.objects.filter(student=student).delete()

        # Delete the student and user records
        student.delete()
        user.delete()

        messages.success(request, "Student deleted successfully!")
        return JsonResponse({'message': 'Student deleted successfully'})
    except Exception as e:
        messages.error(request, f"Error deleting student: {str(e)}")
        return JsonResponse({'message': f"Error deleting student: {str(e)}"}, status=500)
    return redirect('manage_student')

@csrf_exempt
def get_attendance(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        attendance = Attendance.objects.filter(subject=subject, session=session)
        attendance_list = []
        for attd in attendance:
            data = {
                "id": attd.id,
                "attendance_date": str(attd.date),
                "session": attd.session.id
            }
            attendance_list.append(data)
        return JsonResponse(json.dumps(attendance_list), safe=False)
    except Exception as e:
        return None


@csrf_exempt
def save_attendance_data(request):
    if request.method == 'POST':
        subject_id = request.POST.get('subject_id')
        session_id = request.POST.get('session_id')
        attendance_date = request.POST.get('attendance_date')
        student_ids = request.POST.getlist('student_ids[]')

        logging.info(f"Subject ID: {subject_id}")
        logging.info(f"Session ID: {session_id}")
        logging.info(f"Attendance Date: {attendance_date}")
        logging.info(f"Student IDs: {student_ids}")

        try:
            subject = get_object_or_404(Subject, id=subject_id)
            session = get_object_or_404(Session, id=session_id)

            # Convert attendance_date to a date object
            attendance_date_obj = datetime.strptime(attendance_date, '%Y-%m-%d').date()

            # Validate that the attendance date is within the session dates
            if not (session.start_year <= attendance_date_obj <= session.end_year):
                return JsonResponse({"status": "error", "message": "Attendance date is out of session range"})

            attendance = Attendance.objects.create(subject=subject, session=session, date=attendance_date_obj)

            for student_id in student_ids:
                logging.info(f"Processing student ID: {student_id}")
                try:
                    student = get_object_or_404(Student, id=student_id)
                    status = request.POST.get(f'status_{student_id}', 'False') == 'True'
                    AttendanceReport.objects.create(student=student, attendance=attendance, status=status)
                except Exception as e:
                    logging.error(f"Error processing student ID {student_id}: {str(e)}")
                    messages.error(request, f"Error processing student ID {student_id}: {str(e)}")
                    return JsonResponse({"status": "error", "message": f"Error processing student ID {student_id}: {str(e)}"})

            messages.success(request, "Attendance saved successfully!")
            return JsonResponse({"status": "success"})
        except Exception as e:
            logging.error(f"Error in saving attendance: {str(e)}")
            messages.error(request, f"Error in saving attendance: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Invalid request method"})



def manage_students(request):
    students = Student.objects.all()
    context = {
        'students': students,
    }
    return render(request, 'manage_students.html', context)

def showFirebaseJS(request):
    data = """
    // Give the service worker access to Firebase Messaging.
    // Note that you can only use Firebase Messaging here, other Firebase libraries
    // are not available in the service worker.
    importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-app.js');
    importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-messaging.js');

    // Initialize the Firebase app in the service worker by passing in
    // your app's Firebase config object.
    // https://firebase.google.com/docs/web/setup#config-object
    firebase.initializeApp({
        apiKey: "AIzaSyBarDWWHTfTMSrtc5Lj3Cdw5dEvjAkFwtM",
        authDomain: "sms-with-django.firebaseapp.com",
        databaseURL: "https://sms-with-django.firebaseio.com",
        projectId: "sms-with-django",
        storageBucket: "sms-with-django.appspot.com",
        messagingSenderId: "945324593139",
        appId: "1:945324593139:web:03fa99a8854bbd38420c86",
        measurementId: "G-2F2RXTL9GT"
    });

    // Retrieve an instance of Firebase Messaging so that it can handle background
    // messages.
    const messaging = firebase.messaging();
    messaging.setBackgroundMessageHandler(function (payload) {
        const notification = JSON.parse(payload);
        const notificationOption = {
            body: notification.body,
            icon: notification.icon
        }
        return self.registration.showNotification(payload.notification.title, notificationOption);
    });
    """
    return HttpResponse(data, content_type='application/javascript')

@login_required(login_url='user_login')
def student_feedback(request):
    feedbacks = Feedback.objects.filter(student_id=request.user.id)
    return render(request, 'main_app/student_feedback.html', {'feedbacks': feedbacks})

def about_page(request):
    context = {
        'page_title': 'About DMS',
        'features': [
            {
                'icon': 'fa-qrcode',
                'title': 'QR Code Attendance System',
                'description': 'Our innovative QR code-based attendance system eliminates the need for manual roll calls. Students can simply scan their unique QR codes, making attendance tracking quick and efficient.'
            },
            {
                'icon': 'fa-shield-alt',
                'title': 'Enhanced Security',
                'description': 'Built with robust security measures including secure authentication, data encryption, and role-based access control to protect sensitive information.'
            },
            {
                'icon': 'fa-user-friends',
                'title': 'User-Friendly Interface',
                'description': 'Intuitive and responsive design ensures a smooth experience across all devices. Easy navigation and clear layouts make the system accessible to all users.'
            },
            {
                'icon': 'fa-bell',
                'title': 'Real-time Notifications',
                'description': 'Stay updated with instant notifications for attendance, leave requests, announcements, and more through our integrated notification system.'
            },
            {
                'icon': 'fa-tasks',
                'title': 'Comprehensive Management',
                'description': 'Complete solution for managing students, staff, courses, subjects, attendance, and academic records in one centralized platform.'
            },
            {
                'icon': 'fa-calendar-check',
                'title': 'Leave Management',
                'description': 'Streamlined process for handling leave requests with automated approval workflows and status tracking.'
            },
            {
                'icon': 'fa-nfc',
                'title': 'NFC Attendance',
                'description': 'Modern NFC-based attendance tracking system for quick and secure attendance marking.'
            }
        ]
    }
    
    # Choose template based on user type
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            template = 'admin_template/about.html'
        elif request.user.user_type == '2':
            template = 'staff_template/about.html'
        else:
            template = 'student_template/about.html'
    else:
        template = 'main_app/about.html'
        
    return render(request, template, context)