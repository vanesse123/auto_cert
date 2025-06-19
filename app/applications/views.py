from flask import Blueprint, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone
from .. import db
from ..models import Course, Application
from . import applications

@applications.route('/courses/<int:course_number>/apply', methods=['POST'])
@login_required
def apply_course(course_number):
    """課程報名處理"""
    # 獲取課程資訊
    course = Course.query.get_or_404(course_number)
    now = datetime.now(timezone.utc)

    # 檢查是否為管理者
    if current_user.role.name == 'agency':
        flash('管理者無法報名課程', 'warning')
        return redirect(url_for('courses.view_course', course_number=course_number))


    # 檢查是否已報名
    existing_application = Application.query.filter_by(
        employee_number=current_user.employee_number,
        course_number=course_number
    ).first()
    
    if existing_application:
        flash('您已經報名過此課程', 'warning')
        return redirect(url_for('courses.view_course', course_number=course_number))
    

    signup_start = course.get_signup_start_utc()
    signup_deadline = course.get_signup_deadline_utc()
    # 檢查報名時間
    if now < signup_start:
        flash('報名尚未開始', 'warning')
        return redirect(url_for('courses.view_course', course_number=course_number))
    
    if now > signup_deadline:
        flash('報名已經結束', 'warning')
        return redirect(url_for('courses.view_course', course_number=course_number))
    
    # 檢查剩餘名額
    if course.available_slots <= 0:
        flash('課程名額已滿', 'warning')
        return redirect(url_for('courses.view_course', course_number=course_number))
    
    try:
        # 建立報名記錄
        application = Application(
            employee_number=current_user.employee_number,
            course_number=course_number,
            sign_in_state=False,
            create_at=now
        )
        
        db.session.add(application)
        db.session.commit()
        
        # 記錄日誌
        current_app.logger.info(
            f"使用者 {current_user.employee_number} ({current_user.full_name}) "
            f"報名課程 {course_number} ({course.title})"
        )
        
        flash('報名成功！', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"課程報名失敗 - 使用者: {current_user.employee_number}, "
            f"課程: {course_number}, 錯誤: {str(e)}"
        )
        flash('報名失敗，請稍後再試', 'error')
    
    return redirect(url_for('courses.view_course', course_number=course_number))

@applications.route('/courses/<int:course_number>/cancel', methods=['POST'])
@login_required
def cancel_application(course_number):
    """取消報名"""
    # 獲取報名記錄
    application = Application.query.filter_by(
        employee_number=current_user.employee_number,
        course_number=course_number
    ).first_or_404()
    
    # 檢查是否可以取消報名（例如：在課程開始前）
    course = Course.query.get_or_404(course_number)
    now = datetime.now(timezone.utc)
    
    if now.date() >= course.course_start:
        flash('課程已開始，無法取消報名', 'error')
        return redirect(url_for('courses.view_course', course_number=course_number))
    
    try:
        db.session.delete(application)
        db.session.commit()
        
        # 記錄日誌
        current_app.logger.info(
            f"使用者 {current_user.employee_number} ({current_user.full_name}) "
            f"取消報名課程 {course_number} ({course.title})"
        )
        
        flash('已取消報名', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"取消報名失敗 - 使用者: {current_user.employee_number}, "
            f"課程: {course_number}, 錯誤: {str(e)}"
        )
        flash('取消報名失敗，請稍後再試', 'error')
    
    return redirect(url_for('courses.view_course', course_number=course_number))