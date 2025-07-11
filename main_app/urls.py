"""Delta_management_system URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import hod_views, staff_views, student_views, views, nfc_views
from django.urls import path
from .views import get_student_attendance_data, get_recent_attendance


urlpatterns = [
    path("", views.login_page, name='login_page'),
    path('student/qr-code/', student_views.student_qr_code, name='student_qr_code'),
    path('export-attendance-excel/', views.export_attendance_excel, name='export_attendance_excel'),
    path('export-students-excel/', views.export_students_excel, name='export_students_excel'),
    path('download-student-template/', hod_views.download_student_template, name='download_student_template'),
    path('import-students-excel/', hod_views.import_students_from_excel, name='import_students_excel'),
    path("get_attendance", views.get_attendance, name='get_attendance'),
    path("firebase-messaging-sw.js", views.showFirebaseJS, name='showFirebaseJS'),
    path("doLogin/", views.doLogin, name='user_login'),
    path("logout_user/", views.logout_user, name='user_logout'),
    path("admin/home/", hod_views.admin_home, name='admin_home'),
    path("staff/add", hod_views.add_staff, name='add_staff'),
    path("course/add", hod_views.add_course, name='add_course'),
    path("send_student_notification/", hod_views.send_student_notification,
         name='send_student_notification'),
    path("send_staff_notification/", hod_views.send_staff_notification,
         name='send_staff_notification'),
    path("add_session/", hod_views.add_session, name='add_session'),
    path("admin_notify_student", hod_views.admin_notify_student,
         name='admin_notify_student'),
    path("admin_notify_staff", hod_views.admin_notify_staff,
         name='admin_notify_staff'),
    path("admin_view_profile", hod_views.admin_view_profile,
         name='admin_view_profile'),
    path("check_email_availability", hod_views.check_email_availability,
         name="check_email_availability"),
    path("session/manage/", hod_views.manage_session, name='manage_session'),
    path("session/edit/<int:session_id>",
         hod_views.edit_session, name='edit_session'),
    path("student/view/feedback/", hod_views.student_feedback_message,
         name="student_feedback_message",),
    path("staff/view/feedback/", hod_views.staff_feedback_message,
         name="staff_feedback_message",),
    path("student/view/leave/", hod_views.view_student_leave,
         name="view_student_leave",),
    path("staff/view/leave/", hod_views.view_staff_leave, name="view_staff_leave",),
    path("attendance/view/", hod_views.admin_view_attendance,
         name="admin_view_attendance",),
    path("attendance/fetch/", hod_views.get_admin_attendance,
         name='get_admin_attendance'),
    path("student/add/", hod_views.add_student, name='add_student'),
    path("subject/add/", hod_views.add_subject, name='add_subject'),
    path("staff/manage/", hod_views.manage_staff, name='manage_staff'),
    path("student/manage/", hod_views.manage_student, name='manage_student'),
    path("course/manage/", hod_views.manage_course, name='manage_course'),
    path("subject/manage/", hod_views.manage_subject, name='manage_subject'),
    path("staff/edit/<int:staff_id>", hod_views.edit_staff, name='edit_staff'),
    path("staff/delete/<int:staff_id>",
         hod_views.delete_staff, name='delete_staff'),
    path("course/delete/<int:course_id>",
         hod_views.delete_course, name='delete_course'),
    path("subject/delete/<int:subject_id>",
         hod_views.delete_subject, name='delete_subject'),
    path("session/delete/<int:session_id>",
         hod_views.delete_session, name='delete_session'),
    path("student/delete/<int:student_id>",
         hod_views.delete_student, name='delete_student'),
    path("student/delete/multiple/",
         hod_views.delete_multiple_students, name='delete_multiple_students'),
    path("student/edit/<int:student_id>",
         hod_views.edit_student, name='edit_student'),
    path("course/edit/<int:course_id>",
         hod_views.edit_course, name='edit_course'),
    path("subject/edit/<int:subject_id>",
         hod_views.edit_subject, name='edit_subject'),
    path("generate_qr_codes/", hod_views.generate_qr_codes,
         name='generate_qr_codes'),
    path("get_subjects_for_course/", hod_views.get_subjects_for_course, 
         name='get_subjects_for_course'),


    # Staff
path("staff/home/", staff_views.staff_home,
      name='staff_home'),
path("staff/apply/leave/", staff_views.staff_apply_leave,
      name='staff_apply_leave'),
path("staff/feedback/", staff_views.staff_feedback, name='staff_feedback'),
path("staff/view/profile/", staff_views.staff_view_profile,
      name='staff_view_profile'),
path("staff/attendance/take/qr/", staff_views.staff_take_attendance_by_qr,
      name='staff_take_attendance_by_qr'),
path("staff/get_student_information/", staff_views.get_student_information, 
     name='staff_get_student_information'),
path("staff/attendance/view/", staff_views.staff_view_attendance,
    name='staff_view_attendance'),
path("staff/attendance/fetch/", staff_views.get_student_attendance,
    name='get_student_attendance'),
path("staff/attendance/update/", staff_views.update_attendance_status,
    name='update_attendance_status'),
path("staff/attendance/delete/", staff_views.delete_attendance,
    name='delete_attendance'),
path("staff/students/", staff_views.get_enrolled_students,
    name='get_students'),
path("staff/fcmtoken/", staff_views.staff_fcmtoken, 
     name='staff_fcmtoken'),
path("staff/view/notification/", staff_views.staff_view_notification,
      name="staff_view_notification"),
path("staff/recent_attendance/", staff_views.get_recent_attendance_records,
     name="staff_recent_attendance"),
path("staff/export_attendance/", staff_views.export_attendance_to_excel,
     name="staff_export_attendance"),
path('staff/start_attendance_session/', staff_views.start_attendance_session, name='start_attendance_session'),
path('staff/stop_attendance_session/', staff_views.stop_attendance_session, name='stop_attendance_session'),
path('staff/get_attendance_session_status/', staff_views.get_attendance_session_status, name='get_attendance_session_status'),




    # Student
    path('get_student_attendance_data/', get_student_attendance_data, name='get_student_attendance_data'),
    path('get_recent_attendance/', get_recent_attendance, name='get_recent_attendance'),    path("student/home/", student_views.student_home, name='student_home'),
    path("student/view/attendance/", student_views.student_view_attendance,
         name='student_view_attendance'),
    path("student/apply/leave/", student_views.student_apply_leave,
         name='student_apply_leave'),
    path("student/feedback/", student_views.student_feedback,
         name='student_feedback'),
    path("student/view/profile/", student_views.student_view_profile,
         name='student_view_profile'),
    path("student/fcmtoken/", student_views.student_fcmtoken,
         name='student_fcmtoken'),
    path("student/view/notification/", student_views.student_view_notification,
         name="student_view_notification"),
    # Removed student result view path
    path("get_enrolled_students/", staff_views.get_enrolled_students, name='get_enrolled_students'),
    
    # NFC API Endpoints
    path("api/nfc/status/", nfc_views.nfc_status, name='nfc_status'),
    path("api/nfc/read/", nfc_views.nfc_read, name='nfc_read'),
    path("api/nfc/stop/", nfc_views.nfc_stop, name='nfc_stop'),
]
