import json
from datetime import datetime

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404
from .forms import *
from .models import *


def staff_home(request):
    staff = get_object_or_404(Staff, admin=request.user)
    total_students = Student.objects.filter(course=staff.course).count()
    total_leave = LeaveReportStaff.objects.filter(staff=staff).count()
    subjects = Subject.objects.filter(staff=staff)
    total_subject = subjects.count()
    attendance_list = Attendance.objects.filter(subject__in=subjects)
    total_attendance = attendance_list.count()
    attendance_list = []
    subject_list = []
    for subject in subjects:
        attendance_count = Attendance.objects.filter(subject=subject).count()
        subject_list.append(subject.name)
        attendance_list.append(attendance_count)
    context = {
        'page_title': 'Staff Panel - ' + str(staff.admin.last_name) + ' (' + str(staff.course) + ')',
        'total_students': total_students,
        'total_attendance': total_attendance,
        'total_leave': total_leave,
        'total_subject': total_subject,
        'subject_list': subject_list,
        'attendance_list': attendance_list
    }
    return render(request, 'staff_template/home_content.html', context)


def staff_take_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff_id=staff)
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Take Attendance'
    }

    return render(request, 'staff_template/staff_take_attendance.html', context)


@csrf_exempt
def staff_take_attendance_by_qr(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        subject_id = request.POST.get('subject_id')
        attendance_date = request.POST.get('attendance_date')
        
        if not all([student_id, subject_id, attendance_date]):
            missing = []
            if not student_id: missing.append('student_id')
            if not subject_id: missing.append('subject_id')
            if not attendance_date: missing.append('attendance_date')
            return JsonResponse({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing)}'
            })
        
        try:
            # First try to find student by student_code
            student = None
            try:
                student = Student.objects.select_related(
                    'admin', 
                    'session',
                    'course'
                ).get(admin__student_code=student_id)
            except Student.DoesNotExist:
                try:
                    student = Student.objects.select_related(
                        'admin', 
                        'session',
                        'course'
                    ).get(id=student_id)
                except Student.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'No student found with ID or code: {student_id}'
                    })
            
            if not student.session:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Student does not have a session assigned'
                })

            # Get the subject
            try:
                staff = Staff.objects.get(admin=request.user)
                subject = Subject.objects.select_related('course').get(
                    id=subject_id,
                    staff=staff  # This ensures the staff member can only take attendance for their subjects
                )
                
                print(f"[DEBUG] Student: {student.admin.first_name} {student.admin.last_name}")
                print(f"[DEBUG] Student Course: {student.course.name if student.course else 'None'}")
                print(f"[DEBUG] Subject: {subject.name}")
                print(f"[DEBUG] Subject Course: {subject.course.name if subject.course else 'None'}")
                
                # Check if attendance already exists for this student on this date
                attendance_date_obj = datetime.strptime(attendance_date, '%Y-%m-%d').date()
                existing_attendance = Attendance.objects.filter(
                    subject=subject,
                    date=attendance_date_obj
                ).first()
                
                if existing_attendance:
                    # Check if student already has attendance for this date
                    if AttendanceReport.objects.filter(
                        student=student,
                        attendance=existing_attendance
                    ).exists():
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Attendance already marked for this student today'
                        })
                else:
                    # Create new attendance record
                    existing_attendance = Attendance.objects.create(
                        subject=subject,
                        session=student.session,
                        date=attendance_date_obj
                    )
                
                # Create attendance report
                attendance_report = AttendanceReport.objects.create(
                    student=student,
                    attendance=existing_attendance,
                    status=True
                )
                
                # Store the last successful attendance in session
                request.session['last_attendance'] = {
                    'student_name': f"{student.admin.first_name} {student.admin.last_name}",
                    'subject': subject.name,
                    'date': attendance_date,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                session_str = student.session.start_year.strftime('%Y-%m-%d') + " to " + student.session.end_year.strftime('%Y-%m-%d')
                return JsonResponse({
                    'status': 'success',
                    'message': 'Attendance recorded successfully',
                    'student_name': f"{student.admin.first_name} {student.admin.last_name}",
                    'session': session_str
                })
                
            except ValueError as e:
                print(f"[DEBUG] Date error: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid date format: {attendance_date}. Expected format: YYYY-MM-DD'
                })
            except Exception as e:
                print(f"[DEBUG] Error recording attendance: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error recording attendance: {str(e)}'
                })
            
        except Exception as e:
            import traceback
            print(f"Error in staff_take_attendance_by_qr: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({
                'status': 'error',
                'message': f'Error recording attendance: {str(e)}'
            })
    
    subjects = Subject.objects.filter(staff__admin=request.user)
    last_attendance = request.session.get('last_attendance', None)
    if last_attendance:
        del request.session['last_attendance']
        request.session.modified = True
    
    context = {
        'subjects': subjects,
        'page_title': 'Take Attendance by QR Code',
        'last_attendance': last_attendance
    }
    return render(request, 'staff_template/staff_take_attendance_by_qr.html', context)

@csrf_exempt
def get_students(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')

    if not subject_id or not session_id:
        return JsonResponse({
            'error': 'Both subject and session are required'
        }, status=400)

    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)

        # Get students for this course and session
        students = Student.objects.filter(
            course_id=subject.course.id,
            session=session
        ).select_related('admin')  # Use select_related for better performance

        # Debug information
        print(f"Subject: {subject.name}, Course: {subject.course.name}")
        print(f"Session: {session}")
        print(f"Found {students.count()} students")

        student_data = []
        for student in students:
            data = {
                "id": student.id,
                "name": f"{student.admin.first_name} {student.admin.last_name}"
            }
            student_data.append(data)

        return JsonResponse(student_data, safe=False)

    except Subject.DoesNotExist:
        return JsonResponse({
            'error': f'Subject with id {subject_id} does not exist'
        }, status=404)
    except Session.DoesNotExist:
        return JsonResponse({
            'error': f'Session with id {session_id} does not exist'
        }, status=404)
    except Exception as e:
        print(f"Error in get_students: {str(e)}")
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)

@csrf_exempt
def student_details(request):
    student_id = request.POST.get('student_id')
    if not student_id:
        return JsonResponse({'error': 'Student ID is required'}, status=400)

    try:
        # Try to find student by student_code first
        try:
            student = Student.objects.select_related('admin', 'session_year').get(admin__student_code=student_id)
        except Student.DoesNotExist:
            # If not found by student_code, try finding by ID
            try:
                student = Student.objects.select_related('admin', 'session_year').get(admin__id=student_id)
            except Student.DoesNotExist:
                return JsonResponse({'error': 'Student not found'}, status=404)

        return JsonResponse({
            'id': student.admin.id,
            'name': f"{student.admin.first_name} {student.admin.last_name}",
            'session': f"{student.session_year.session_start_year} - {student.session_year.session_end_year}"
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@csrf_exempt
def save_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    students = json.loads(student_data)
    try:
        session = get_object_or_404(Session, id=session_id)
        subject = get_object_or_404(Subject, id=subject_id)
        
        # Convert date string to date object
        attendance_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Validate that the attendance date is within the session dates
        if not (session.start_year <= attendance_date <= session.end_year):
            return JsonResponse({"status": "error", "message": "Attendance date is out of session range"})
            
        attendance = Attendance(session=session, subject=subject, date=date)
        attendance.save()

        for student_dict in students:
            student = get_object_or_404(Student, id=student_dict.get('id'))
            attendance_report = AttendanceReport(student=student, attendance=attendance, status=student_dict.get('status'))
            attendance_report.save()
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

    return HttpResponse("OK")

@csrf_exempt
def save_attendance_qr(request):
    try:
        student_id = request.POST.get('student_id')
        date = request.POST.get('date')
        subject_id = request.POST.get('subject')
        session_id = request.POST.get('session')

        if not all([student_id, date, subject_id, session_id]):
            return JsonResponse({"error": "Missing required parameters"}, status=400)

        session = get_object_or_404(Session, id=session_id)
        subject = get_object_or_404(Subject, id=subject_id)
        student = get_object_or_404(Student, admin_id=student_id, course_id=subject.course.id, session_id=session_id)

        # Convert date string to date object
        attendance_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Validate that the attendance date is within the session dates
        if not (session.start_year <= attendance_date <= session.end_year):
            return JsonResponse({"error": "Attendance date is out of session range"}, status=400)

        attendance, created = Attendance.objects.get_or_create(session=session, subject=subject, date=date)

        attendance_report, created = AttendanceReport.objects.get_or_create(
            student=student, attendance=attendance, defaults={"status": 1}
        )

        return JsonResponse({"message": "Attendance recorded successfully"}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

def staff_update_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff_id=staff)
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Update Attendance'
    }

    return render(request, 'staff_template/staff_update_attendance.html', context)


@csrf_exempt
def get_student_attendance(request):
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        date = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_data = AttendanceReport.objects.filter(attendance=date)
        student_data = []
        for attendance in attendance_data:
            data = {"id": attendance.student.admin.id,
                    "name": attendance.student.admin.first_name + " " + attendance.student.admin.last_name,
                    "status": attendance.status}
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e


@csrf_exempt
def update_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    students = json.loads(student_data)
    try:
        attendance = get_object_or_404(Attendance, id=date)

        for student_dict in students:
            student = get_object_or_404(
                Student, admin_id=student_dict.get('id'))
            attendance_report = get_object_or_404(AttendanceReport, student=student, attendance=attendance)
            attendance_report.status = student_dict.get('status')
            attendance_report.save()
    except Exception as e:
        return None

    return HttpResponse("OK")


def staff_apply_leave(request):
    form = LeaveReportStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStaff.objects.filter(staff=staff),
        'page_title': 'Apply for Leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('staff_apply_leave'))
            except Exception:
                messages.error(request, "Could not apply!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_apply_leave.html", context)


def staff_feedback(request):
    form = FeedbackStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStaff.objects.filter(staff=staff),
        'page_title': 'Add Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(request, "Feedback submitted for review")
                return redirect(reverse('staff_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_feedback.html", context)


def staff_view_profile(request):
    staff = get_object_or_404(Staff, admin=request.user)
    form = StaffEditForm(request.POST or None, request.FILES or None,instance=staff)
    context = {'form': form, 'page_title': 'View/Update Profile'}
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = staff.admin
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
                staff.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('staff_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
                return render(request, "staff_template/staff_view_profile.html", context)
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
            return render(request, "staff_template/staff_view_profile.html", context)

    return render(request, "staff_template/staff_view_profile.html", context)


@csrf_exempt
def staff_fcmtoken(request):
    token = request.POST.get('token')
    try:
        staff_user = get_object_or_404(CustomUser, id=request.user.id)
        staff_user.fcm_token = token
        staff_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def staff_view_notification(request):
    staff = get_object_or_404(Staff, admin=request.user)
    notifications = NotificationStaff.objects.filter(staff=staff)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "staff_template/staff_view_notification.html", context)


def staff_add_result(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    sessions = Session.objects.all()
    context = {
        'page_title': 'Result Upload',
        'subjects': subjects,
        'sessions': sessions
    }
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_list')
            subject_id = request.POST.get('subject')
            test = request.POST.get('test')
            exam = request.POST.get('exam')
            student = get_object_or_404(Student, id=student_id)
            subject = get_object_or_404(Subject, id=subject_id)
            try:
                data = StudentResult.objects.get(
                    student=student, subject=subject)
                data.exam = exam
                data.test = test
                data.save()
                messages.success(request, "Scores Updated")
            except:
                result = StudentResult(student=student, subject=subject, test=test, exam=exam)
                result.save()
                messages.success(request, "Scores Saved")
        except Exception as e:
            messages.warning(request, "Error Occured While Processing Form")
    return render(request, "staff_template/staff_add_result.html", context)


@csrf_exempt
def fetch_student_result(request):
    try:
        subject_id = request.POST.get('subject')
        student_id = request.POST.get('student')
        student = get_object_or_404(Student, id=student_id)
        subject = get_object_or_404(Subject, id=subject_id)
        result = StudentResult.objects.get(student=student, subject=subject)
        result_data = {
            'exam': result.exam,
            'test': result.test
        }
        return HttpResponse(json.dumps(result_data))
    except Exception as e:
        return HttpResponse('False')

@csrf_exempt
def staff_get_student_session(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed", status=405)
    
    student_id = request.POST.get('student_id')
    print(f"[DEBUG] Received student_id: {student_id}")  # Debug log
    
    if not student_id:
        return JsonResponse({'error': 'Student ID is required'}, status=400)

    try:
        # Try to find student by student_code first
        student = None
        try:
            print(f"[DEBUG] Attempting to find student by student_code: {student_id}")
            student = Student.objects.select_related(
                'admin', 
                'session',
                'course'
            ).get(admin__student_code=student_id)
            print(f"[DEBUG] Found student by code: {student.admin.first_name} {student.admin.last_name}")
        except Student.DoesNotExist:
            # If not found by student_code, try finding by ID
            try:
                print(f"[DEBUG] Attempting to find student by ID: {student_id}")
                student = Student.objects.select_related(
                    'admin', 
                    'session',
                    'course'
                ).get(id=student_id)
                print(f"[DEBUG] Found student by ID: {student.admin.first_name} {student.admin.last_name}")
            except (Student.DoesNotExist, ValueError):
                print(f"[DEBUG] Student not found with code or ID: {student_id}")
                return JsonResponse({
                    'error': 'Student not found',
                    'details': 'No student found with the provided ID or code. Please verify the ID and try again.'
                }, status=404)

        if not student:
            return JsonResponse({
                'error': 'Student not found',
                'details': 'Unable to locate student record.'
            }, status=404)

        # Get student details
        if not student.session:
            print(f"[DEBUG] No session found for student: {student.admin.first_name} {student.admin.last_name}")
            # Try to find the latest session
            latest_session = Session.objects.order_by('-start_year').first()
            if latest_session:
                student.session = latest_session
                student.save()
                print(f"[DEBUG] Assigned latest session to student: {latest_session}")
            else:
                return JsonResponse({
                    'error': 'No session assigned',
                    'details': 'This student does not have a session assigned.'
                }, status=400)

        session_str = student.session.start_year.strftime('%Y-%m-%d') + " to " + student.session.end_year.strftime('%Y-%m-%d')
        student_data = {
            'name': f"{student.admin.first_name} {student.admin.last_name}",
            'session': session_str,
            'course': student.course.name if student.course else None,
            'session_id': student.session.id if student.session else None
        }
        print(f"[DEBUG] Returning student data: {student_data}")
        return JsonResponse(student_data)

    except Exception as e:
        print(f"[DEBUG] Error in staff_get_student_session: {str(e)}")
        import traceback
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        return JsonResponse({
            'error': 'An error occurred while looking up the student',
            'details': str(e)
        }, status=500)
