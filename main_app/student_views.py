import json
import math
import qrcode
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,
                              redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from .forms import *
from .models import *


def student_home(request):
    student = get_object_or_404(Student, admin=request.user)
    total_subject = Subject.objects.filter(course=student.course).count()
    total_attendance = AttendanceReport.objects.filter(student=student).count()
    total_present = AttendanceReport.objects.filter(student=student, status=True).count()
    if total_attendance == 0:  # Don't divide. DivisionByZero
        percent_absent = percent_present = 0
    else:
        percent_present = math.floor((total_present/total_attendance) * 100)
        percent_absent = math.ceil(100 - percent_present)
    subject_name = []
    data_present = []
    data_absent = []
    subjects = Subject.objects.filter(course=student.course)
    for subject in subjects:
        attendance = Attendance.objects.filter(subject=subject)
        present_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=True, student=student).count()
        absent_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=False, student=student).count()
        subject_name.append(subject.name)
        data_present.append(present_count)
        data_absent.append(absent_count)
    context = {
        'student': student,  # Added student object to context
        'total_attendance': total_attendance,
        'percent_present': percent_present,
        'percent_absent': percent_absent,
        'total_subject': total_subject,
        'subjects': subjects,
        'data_present': data_present,
        'data_absent': data_absent,
        'data_name': subject_name,
        'page_title': 'Student Homepage'
    }
    return render(request, 'student_template/home_content.html', context)


@csrf_exempt
def student_view_attendance(request):
    # Get student data associated with the current user
    student = get_object_or_404(Student, admin=request.user)
    
    if request.method != 'POST':
        # GET request - show the attendance view form
        course = get_object_or_404(Course, id=student.course.id) 
        # Pass the student object to the template context to display session info
        context = {
            'subjects': Subject.objects.filter(course=course),
            'student': student.admin,  # This gives access to admin fields (first_name, last_name, etc.)
            'page_title': 'View Attendance'
        }
        return render(request, 'student_template/student_view_attendance.html', context)
    else:
        # POST request - fetch attendance data
        subject_id = request.POST.get('subject')
        
        try:
            subject = get_object_or_404(Subject, id=subject_id)
            
            # Get all attendance objects for this subject
            attendance_records = Attendance.objects.filter(subject=subject)
            
            # Get attendance reports for this student within the selected attendance records
            attendance_reports = AttendanceReport.objects.filter(
                attendance__in=attendance_records, student=student)
            
            # Format data for JSON response
            json_data = []
            for report in attendance_reports:
                data = {
                    "id": report.id,
                    "date": str(report.attendance.date),
                    "status": report.status,
                    "subject_name": report.attendance.subject.name
                }
                json_data.append(data)
                
            return JsonResponse(json_data, safe=False)
            
        except Exception as e:
            # Log the error for debugging
            import logging
            logging.error(f"Error in student_view_attendance: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

def student_apply_leave(request):
    form = LeaveReportStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStudent.objects.filter(student=student),
        'page_title': 'Apply for leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('student_apply_leave'))
            except Exception:
                messages.error(request, "Could not submit")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "student_template/student_apply_leave.html", context)


def student_feedback(request):
    form = FeedbackStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStudent.objects.filter(student=student),
        'page_title': 'Student Feedback'

    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(
                    request, "Feedback submitted for review")
                return redirect(reverse('student_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "student_template/student_feedback.html", context)


def student_view_profile(request):
    student = get_object_or_404(Student, admin=request.user)
    form = StudentEditForm(request.POST or None, request.FILES or None,
                           instance=student)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = student.admin
                if password != None:
                    admin.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = passport_url
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                student.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('student_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(request, "Error Occured While Updating Profile " + str(e))

    return render(request, "student_template/student_view_profile.html", context)


@csrf_exempt
def student_fcmtoken(request):
    token = request.POST.get('token')
    student_user = get_object_or_404(CustomUser, id=request.user.id)
    try:
        student_user.fcm_token = token
        student_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def student_view_notification(request):
    student = get_object_or_404(Student, admin=request.user)
    notifications = NotificationStudent.objects.filter(student=student)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "student_template/student_view_notification.html", context)


def student_view_result(request):
    student = get_object_or_404(Student, admin=request.user)
    results = StudentResult.objects.filter(student=student)
    context = {
        'results': results,
        'page_title': "View Results"
    }
    return render(request, "student_template/student_view_result.html", context)

      
@login_required
def student_qr_code(request):
    student = get_object_or_404(Student, admin=request.user)
    
    # Generate QR code data - only include student_code
    student_data = {
        'student_code': student.admin.student_code
    }
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(student_data))
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Create a new image with padding for text
    canvas_width = qr_img.size[0]
    canvas_height = qr_img.size[1] + 60
    canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
    
    # Paste QR code on canvas
    canvas.paste(qr_img, (0, 0))
    
    # Add student info text
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        font = ImageFont.load_default()
    
    # Add student name and ID
    student_name = f"{student.admin.first_name} {student.admin.last_name}"
    id_text = f"ID: {student.admin.student_code}"
    
    # Center the text
    student_name_width = draw.textlength(student_name, font=font)
    id_text_width = draw.textlength(id_text, font=font)
    
    draw.text(
        ((canvas_width - student_name_width) // 2, qr_img.size[1] + 10),
        student_name,
        fill="black",
        font=font
    )
    draw.text(
        ((canvas_width - id_text_width) // 2, qr_img.size[1] + 35),
        id_text,
        fill="black",
        font=font
    )
    
    # Return image response
    response = HttpResponse(content_type="image/png")
    canvas.save(response, "PNG")
    return response



