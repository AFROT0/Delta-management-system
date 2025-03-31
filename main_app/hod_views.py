# Standard library imports
import json
import logging
import random
import string
from datetime import datetime
from io import BytesIO
import os

# Third-party imports
import requests
from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView
from django.db import transaction
try:
   import qrcode
except ImportError:
    qrcode = None

# Local application imports
from .forms import *
from .models import (
    Admin, Attendance, AttendanceReport, Course, CustomUser,
    FeedbackStaff, FeedbackStudent, LeaveReportStaff,
    LeaveReportStudent, NotificationStaff, NotificationStudent,
    Session, Staff, Student, StudentResult, Subject
)


def admin_home(request):
    total_staff = Staff.objects.all().count()
    total_students = Student.objects.all().count()
    subjects = Subject.objects.all()
    total_subject = subjects.count()
    total_course = Course.objects.all().count()
    
    # Attendance per subject
    subject_list = []
    attendance_list = []
    for subject in subjects:
        attendance_count = Attendance.objects.filter(subject=subject).count()
        subject_list.append(subject.name[:7])
        attendance_list.append(attendance_count)

    # Students per course
    course_all = Course.objects.all()
    course_name_list = []
    student_count_list_in_course = []
    for course in course_all:
        students = Student.objects.filter(course_id=course.id).count()
        course_name_list.append(course.name)
        student_count_list_in_course.append(students)
    
    # Students per subject
    subject_all = Subject.objects.all()
    subject_list = []
    student_count_list_in_subject = []
    for subject in subject_all:
        course = Course.objects.get(id=subject.course.id)
        student_count = Student.objects.filter(course_id=course.id).count()
        subject_list.append(subject.name)
        student_count_list_in_subject.append(student_count)

    # Student attendance statistics
    student_attendance_present_list = []
    student_attendance_leave_list = []
    student_name_list = []
    students = Student.objects.all()
    for student in students:
        attendance = AttendanceReport.objects.filter(student_id=student.id, status=True).count()
        absent = AttendanceReport.objects.filter(student_id=student.id, status=False).count()
        leave = LeaveReportStudent.objects.filter(student_id=student.id, status=1).count()
        student_attendance_present_list.append(attendance)
        student_attendance_leave_list.append(leave + absent)
        student_name_list.append(f"{student.admin.first_name} {student.admin.last_name}")

    context = {
        'page_title': "Administrative Dashboard",
        'total_students': total_students,
        'total_staff': total_staff,
        'total_course': total_course,
        'total_subject': total_subject,
        'subject_list': subject_list,
        'attendance_list': attendance_list,
        'student_attendance_present_list': student_attendance_present_list,
        'student_attendance_leave_list': student_attendance_leave_list,
        'student_name_list': student_name_list,
        'student_count_list_in_subject': student_count_list_in_subject,
        'student_count_list_in_course': student_count_list_in_course,
        'course_name_list': course_name_list,
    }
    return render(request, 'hod_template/home_content.html', context)


def add_staff(request):
    form = StaffForm(request.POST or None, request.FILES or None)
    context = {'form': form, 'page_title': 'Add Staff'}
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password')
            course = form.cleaned_data.get('course')
            passport = request.FILES.get('profile_pic')
            
            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=2, first_name=first_name, last_name=last_name)
                user.gender = gender
                user.address = address
                user.staff.course = course
                
                if passport:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    user.profile_pic = passport_url
                
                user.save()
                messages.success(request, "Staff added successfully!")
                return redirect(reverse('add_staff'))
            except Exception as e:
                messages.error(request, f"Could not add staff: {str(e)}")
        else:
            messages.error(request, "Please fill all required fields")

    return render(request, 'hod_template/add_staff_template.html', context)


def add_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                address = form.cleaned_data.get('address')
                email = form.cleaned_data.get('email')
                password = form.cleaned_data.get('password')
                course = form.cleaned_data.get('course')
                gender = form.cleaned_data.get('gender')
                session = form.cleaned_data.get('session')
                
                # Generate a unique student code
                student_code = generate_unique_student_code()
                
                # Create user first
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=3,
                    first_name=first_name, last_name=last_name)
                user.gender = gender
                user.address = address
                user.student.course = course
                user.student.session = session
                user.student_code = student_code
                
                # Handle profile picture if provided
                if 'profile_pic' in request.FILES:
                    profile_pic = request.FILES['profile_pic']
                    fs = FileSystemStorage()
                    filename = fs.save(profile_pic.name, profile_pic)
                    user.profile_pic = fs.url(filename)
                
                # Save user to get the ID
                user.save()
                
                # Instead of creating a new Student, get the one created by the signal
                student = Student.objects.get(admin=user)
                student.course = course
                student.session = session
                student.save()
                
                try:
                    # Generate QR code with student data
                    student_data = {
                        'student_code': student_code,
                        'name': f"{first_name} {last_name}",
                        'email': email
                    }
                    
                    if qrcode is not None:
                        print("Starting QR code generation...")  # Debug log
                        # Create QR code
                        qr = qrcode.QRCode(
                            version=1,
                            error_correction=qrcode.constants.ERROR_CORRECT_L,
                            box_size=10,
                            border=4,
                        )
                        qr.add_data(json.dumps(student_data))
                        qr.make(fit=True)
                        qr_image = qr.make_image(fill_color="black", back_color="white")
                        
                        # Save QR code
                        buffer = BytesIO()
                        qr_image.save(buffer, format='PNG')
                        buffer.seek(0)
                        
                        # Create a unique filename for the QR code
                        filename = f'qr_code_{student_code}.png'
                        file_path = os.path.join('qr_codes', filename)
                        print(f"Saving QR code to path: {file_path}")  # Debug log
                        
                        # Use FileSystemStorage to save the file
                        fs = FileSystemStorage()
                        saved_path = fs.save(file_path, ContentFile(buffer.getvalue()))
                        print(f"QR code saved successfully at: {saved_path}")  # Debug log
                        
                        # Update user's qr_code field with the saved file path
                        user.qr_code = saved_path
                        user.save()
                        print(f"User QR code path updated: {user.qr_code.url}")  # Debug log
                        
                        messages.success(request, f"QR code generated and saved successfully")
                    else:
                        messages.warning(request, "QR code generation is not available. Please install qrcode package.")
                        print("QR code generation failed: qrcode module not available")  # Debug log
                except Exception as qr_error:
                    messages.warning(request, f"Could not generate QR code: {str(qr_error)}")
                    print(f"QR code generation error: {str(qr_error)}")  # Debug log
                
                # Check if request is AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': f'Student {first_name} {last_name} added successfully!'
                    })
                else:
                    messages.success(request, "Successfully Added Student")
                    return redirect(reverse('add_student'))
                    
            except Exception as e:
                # Check if request is AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Could not add student: {str(e)}'
                    }, status=400)
                else:
                    messages.error(request, f"Could Not Add: {str(e)}")
        else:
            # Check if request is AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = dict(form.errors.items())
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please correct the errors below.',
                    'errors': errors
                }, status=400)
            else:
                messages.error(request, "Please Fill All Required Fields!")
    else:
        form = StudentForm()
    
    context = {
        'form': form,
        'page_title': 'Add Student'
    }
    return render(request, 'hod_template/add_student_template.html', context)

def generate_unique_student_code():
    import random
    import string
    
    while True:
        # Generate a 6-character code with only letters and numbers
        characters = string.ascii_letters + string.digits
        code = ''.join(random.choice(characters) for _ in range(6))
        
        # Check if code already exists
        if not CustomUser.objects.filter(student_code=code).exists():
            return code


def add_course(request):
    form = CourseForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Course'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            # Check if course with the same name already exists
            if Course.objects.filter(name__iexact=name).exists():
                messages.error(request, "Course with this name already exists")
            else:
                try:
                    course = Course()
                    course.name = name
                    course.save()
                    messages.success(request, "Successfully Added")
                    return redirect(reverse('add_course'))
                except Exception as e:
                    messages.error(request, f"Could Not Add: {str(e)}")
        else:
            messages.error(request, "Could Not Add: Form is invalid")
    return render(request, 'hod_template/add_course_template.html', context)



def add_subject(request):
    form = SubjectForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Subject'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            course = form.cleaned_data.get('course')
            staff = form.cleaned_data.get('staff')
            
            # Check if subject with the same name already exists in the same course
            if Subject.objects.filter(name__iexact=name, course=course).exists():
                messages.error(request, "Subject with this name already exists in the selected course")
            else:
                try:
                    subject = Subject()
                    subject.name = name
                    subject.staff = staff
                    subject.course = course
                    subject.save()
                    messages.success(request, "Successfully Added")
                    return redirect(reverse('add_subject'))
                except Exception as e:
                    messages.error(request, f"Could Not Add: {str(e)}")
        else:
            messages.error(request, "Please fill all required fields correctly")

    return render(request, 'hod_template/add_subject_template.html', context)


def manage_staff(request):
    allStaff = CustomUser.objects.filter(user_type=2)
    context = {
        'allStaff': allStaff,
        'page_title': 'Manage Staff'
    }
    return render(request, "hod_template/manage_staff.html", context)


def manage_student(request):
    students = CustomUser.objects.filter(user_type=3)
    context = {
        'students': students,
        'page_title': 'Manage Students'
    }
    return render(request, "hod_template/manage_student.html", context)


def manage_course(request):
    courses = Course.objects.all()
    context = {
        'courses': courses,
        'page_title': 'Manage Courses'
    }
    return render(request, "hod_template/manage_course.html", context)


def manage_subject(request):
    subjects = Subject.objects.all()
    context = {
        'subjects': subjects,
        'page_title': 'Manage Subjects'
    }
    return render(request, "hod_template/manage_subject.html", context)


def edit_staff(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id)
    form = StaffForm(request.POST or None, instance=staff)
    context = {
        'form': form,
        'staff_id': staff_id,
        'page_title': 'Edit Staff'
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            course = form.cleaned_data.get('course')
            passport = request.FILES.get('profile_pic') or None
            try:
                user = CustomUser.objects.get(id=staff.admin.id)
                user.username = username
                user.email = email
                if password != None:
                    user.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    user.profile_pic = passport_url
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                user.address = address
                staff.course = course
                user.save()
                staff.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_staff', args=[staff_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Please fil form properly")
    else:
        user = CustomUser.objects.get(id=staff_id)
        staff = Staff.objects.get(id=user.id)
        return render(request, "hod_template/edit_staff_template.html", context)


def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    form = StudentForm(request.POST or None, instance=student)
    context = {
        'form': form,
        'student_id': student_id,
        'page_title': 'Edit Student'
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            course = form.cleaned_data.get('course')
            session = form.cleaned_data.get('session')
            passport = request.FILES.get('profile_pic') or None
            try:
                user = CustomUser.objects.get(id=student.admin.id)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    user.profile_pic = passport_url
                user.username = username
                user.email = email
                if password != None:
                    user.set_password(password)
                user.first_name = first_name
                user.last_name = last_name
                student.session = session
                user.gender = gender
                user.address = address
                student.course = course
                user.save()
                student.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_student', args=[student_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Please Fill Form Properly!")
    else:
        return render(request, "hod_template/edit_student_template.html", context)


def edit_course(request, course_id):
    instance = get_object_or_404(Course, id=course_id)
    form = CourseForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'course_id': course_id,
        'page_title': 'Edit Course'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            try:
                course = Course.objects.get(id=course_id)
                course.name = name
                course.save()
                messages.success(request, "Successfully Updated")
            except:
                messages.error(request, "Could Not Update")
        else:
            messages.error(request, "Could Not Update")

    return render(request, 'hod_template/edit_course_template.html', context)


def edit_subject(request, subject_id):
    instance = get_object_or_404(Subject, id=subject_id)
    form = SubjectForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'subject_id': subject_id,
        'page_title': 'Edit Subject'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            course = form.cleaned_data.get('course')
            staff = form.cleaned_data.get('staff')
            try:
                subject = Subject.objects.get(id=subject_id)
                subject.name = name
                subject.staff = staff
                subject.course = course
                subject.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_subject', args=[subject_id]))
            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
    return render(request, 'hod_template/edit_subject_template.html', context)


def add_session(request):
    form = SessionForm(request.POST or None)
    context = {'form': form, 'page_title': 'Add Session'}
    
    if request.method == 'POST':
        if form.is_valid():
            start_year = form.cleaned_data.get('start_year')
            end_year = form.cleaned_data.get('end_year')
            
            # Check if start date equals end date
            if start_year == end_year:
                messages.error(request, 'Start date cannot be the same as end date')
                return render(request, "hod_template/add_session_template.html", context)
            
            # Check if start date is after end date
            if start_year > end_year:
                messages.error(request, 'Start date cannot be after end date')
                return render(request, "hod_template/add_session_template.html", context)
            
            # Check if session with same dates already exists
            if Session.objects.filter(start_year=start_year, end_year=end_year).exists():
                messages.error(request, 'Session with these dates already exists')
                return render(request, "hod_template/add_session_template.html", context)
            
            try:
                form.save()
                messages.success(request, "Session was created successfully")
                return redirect(reverse('add_session'))
            except Exception as e:
                messages.error(request, f'Failed to add session: {str(e)}')
        else:
            # This shows when form validation fails
            messages.error(request, 'This session already exists')
    
    return render(request, "hod_template/add_session_template.html", context)

def manage_session(request):
    sessions = Session.objects.all()
    context = {'sessions': sessions, 'page_title': 'Manage Sessions'}
    return render(request, "hod_template/manage_session.html", context)


def edit_session(request, session_id):
    instance = get_object_or_404(Session, id=session_id)
    form = SessionForm(request.POST or None, instance=instance)
    context = {'form': form, 'session_id': session_id,
               'page_title': 'Edit Session'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Session Updated")
                return redirect(reverse('edit_session', args=[session_id]))
            except Exception as e:
                messages.error(
                    request, "Session Could Not Be Updated " + str(e))
                return render(request, "hod_template/edit_session_template.html", context)
        else:
            messages.error(request, "Invalid Form Submitted ")
            return render(request, "hod_template/edit_session_template.html", context)

    else:
        return render(request, "hod_template/edit_session_template.html", context)


@csrf_exempt
def check_email_availability(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    email = request.POST.get("email")
    if not email:
        return JsonResponse({'error': 'Email is required'}, status=400)
    
    try:
        # Check if email exists in CustomUser model
        exists = CustomUser.objects.filter(email=email).exists()
        if exists:
            return JsonResponse({
                'is_taken': True,
                'error_message': 'This email is already registered.'
            })
        return JsonResponse({
            'is_taken': False,
            'success_message': 'Email is available.'
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@csrf_exempt
def student_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackStudent.objects.all()
        context = {
            'feedbacks': feedbacks,
            'page_title': 'Student Feedback Messages'
        }
        return render(request, 'hod_template/student_feedback_template.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackStudent, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse(False)


@csrf_exempt
def staff_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackStaff.objects.all()
        context = {
            'feedbacks': feedbacks,
            'page_title': 'Staff Feedback Messages'
        }
        return render(request, 'hod_template/staff_feedback_template.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackStaff, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse(False)


@csrf_exempt
def view_staff_leave(request):
    if request.method != 'POST':
        allLeave = LeaveReportStaff.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Staff'
        }
        return render(request, "hod_template/staff_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportStaff, id=id)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return False


@csrf_exempt
def view_student_leave(request):
    if request.method != 'POST':
        allLeave = LeaveReportStudent.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Students'
        }
        return render(request, "hod_template/student_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportStudent, id=id)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return False


def admin_view_attendance(request):
    subjects = Subject.objects.all()
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'View Attendance'
    }

    return render(request, "hod_template/admin_view_attendance.html", context)


@csrf_exempt
def get_admin_attendance(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        attendance = get_object_or_404(
            Attendance, id=attendance_date_id, session=session)
        attendance_reports = AttendanceReport.objects.filter(
            attendance=attendance)
        json_data = []
        for report in attendance_reports:
            data = {
                "status":  str(report.status),
                "name": str(report.student)
            }
            json_data.append(data)
        return JsonResponse(json.dumps(json_data), safe=False)
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

            # Validate that the attendance date's year is within the session's academic years
            attendance_year = attendance_date_obj.year
            session_start_year = session.start_year.year if isinstance(session.start_year, datetime) else session.start_year
            session_end_year = session.end_year.year if isinstance(session.end_year, datetime) else session.end_year
            
            if not (session_start_year <= attendance_year <= session_end_year):
                return JsonResponse({
                    "status": "error",
                    "message": f"Attendance year {attendance_year} must be between academic session years "
                              f"{session_start_year} and {session_end_year}"
                })

            # Validate that the attendance date is precisely within the session date range
            if attendance_date_obj < session.start_year.date() or attendance_date_obj > session.end_year.date():
                return JsonResponse({
                    "status": "error",
                    "message": f"Attendance date ({attendance_date_obj.strftime('%Y-%m-%d')}) is outside the session period ({session.start_year.date().strftime('%Y-%m-%d')} - {session.end_year.date().strftime('%Y-%m-%d')})"
                })

            # Check if attendance already exists for the given date and student
            for student_id in student_ids:
                student = get_object_or_404(Student, id=student_id)
                if AttendanceReport.objects.filter(student=student, attendance__date=attendance_date_obj).exists():
                    return JsonResponse({"status": "error", "message": f"Attendance already recorded for student {student.admin.first_name} {student.admin.last_name} on {attendance_date}"})

            attendance = Attendance.objects.create(subject=subject, session=session, date=attendance_date_obj)

            # Check if attendance already exists for the given date and student
            for student_id in student_ids:
                student = get_object_or_404(Student, id=student_id)
                if AttendanceReport.objects.filter(student=student, attendance__date=attendance_date_obj).exists():
                    return JsonResponse({"status": "error", "message": f"Attendance already recorded for student {student.admin.first_name} {student.admin.last_name} on {attendance_date}"})
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


def admin_view_profile(request):
    admin = get_object_or_404(Admin, admin=request.user)
    form = AdminForm(request.POST or None, request.FILES or None,
                     instance=admin)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                passport = request.FILES.get('profile_pic') or None
                custom_user = admin.admin
                if password != None:
                    custom_user.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    custom_user.profile_pic = passport_url
                custom_user.first_name = first_name
                custom_user.last_name = last_name
                custom_user.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('admin_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
    return render(request, "hod_template/admin_view_profile.html", context)


def admin_notify_staff(request):
    staff = CustomUser.objects.filter(user_type=2)
    context = {
        'page_title': "Send Notifications To Staff",
        'allStaff': staff
    }
    return render(request, "hod_template/staff_notification.html", context)


def admin_notify_student(request):
    student = CustomUser.objects.filter(user_type=3)
    context = {
        'page_title': "Send Notifications To Students",
        'students': student
    }
    return render(request, "hod_template/student_notification.html", context)


@csrf_exempt
def send_student_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    student = get_object_or_404(Student, admin_id=id)
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "Student Management System",
                'body': message,
                'click_action': reverse('student_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': student.admin.fcm_token
        }
        headers = {'Authorization':
                   'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
                   'Content-Type': 'application/json'}
        data = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationStudent(student=student, message=message)
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


@csrf_exempt
def send_staff_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    staff = get_object_or_404(Staff, admin_id=id)
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "Student Management System",
                'body': message,
                'click_action': reverse('staff_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': staff.admin.fcm_token
        }
        headers = {'Authorization':
                   'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
                   'Content-Type': 'application/json'}
        data = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationStaff(staff=staff, message=message)
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def delete_staff(request, staff_id):
    """
    Delete a staff member and all their related records safely using a transaction.
    Handles updating subjects and cascade deletion of feedback, leave reports, etc.
    
    Args:
        request: HTTP request object
        staff_id: ID of the staff member to delete
        
    Returns:
        Redirects to manage_staff view with success/error message
    """
    staff = get_object_or_404(CustomUser, staff__id=staff_id)
    
    try:
        with transaction.atomic():
            # Store staff name before deletion for message
            staff_name = f"{staff.first_name} {staff.last_name}"
            
            # Get all subjects taught by this staff
            staff_subjects = Subject.objects.filter(staff=staff.staff)
            
            # Delete attendance records for subjects taught by this staff
            attendance_records = Attendance.objects.filter(subject__in=staff_subjects)
            AttendanceReport.objects.filter(attendance__in=attendance_records).delete()
            attendance_records.delete()
            
            # Delete notifications, feedback, and leave reports
            NotificationStaff.objects.filter(staff=staff.staff).delete()
            FeedbackStaff.objects.filter(staff=staff.staff).delete()
            LeaveReportStaff.objects.filter(staff=staff.staff).delete()
            
            # Delete subjects taught by staff
            staff_subjects.delete()
            
            # Delete the staff user which will cascade delete Staff model
            staff.delete()
            
            messages.success(request, f"Staff member '{staff_name}' and all related records deleted successfully!")
            
    except Exception as e:
        messages.error(request, f"Error deleting staff member: {str(e)}")
        
    return redirect(reverse('manage_staff'))

def delete_student(request, student_id):
    """
    Delete a student and all their related records after checking dependencies.
    Handles cascade deletion of attendance records and leave reports.
    """
    student = get_object_or_404(CustomUser, student__id=student_id)
    
    try:
        # Begin transaction
        with transaction.atomic():
            # Delete related records first
            AttendanceReport.objects.filter(student=student.student).delete()
            LeaveReportStudent.objects.filter(student=student.student).delete()
            FeedbackStudent.objects.filter(student=student.student).delete()
            NotificationStudent.objects.filter(student=student.student).delete()
            
            # Delete the student and user
            student_name = f"{student.first_name} {student.last_name}"
            student.delete()
            
            messages.success(request, f"Student '{student_name}' and all related records deleted successfully!")
            
    except Exception as e:
        messages.error(request, f"Error deleting student: {str(e)}")
        
    return redirect(reverse('manage_student'))

def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    try:
        course.delete()
        messages.success(request, "Course deleted successfully!")
    except Exception:
        messages.error(
            request, "Sorry, some students are assigned to this course already. Kindly change the affected student course and try again")
    return redirect(reverse('manage_course'))


def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    subject.delete()
    messages.success(request, "Subject deleted successfully!")
    return redirect(reverse('manage_subject'))


def delete_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    if Student.objects.filter(session=session).exists():
        messages.error(request, "There are students assigned to this session. Please move them to another session.")
    else:
        session.delete()
        messages.success(request, "Session deleted successfully!")
    return redirect(reverse('manage_session'))
