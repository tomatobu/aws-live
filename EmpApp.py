from flask import Flask, render_template,request
from datetime import datetime
from pymysql import connections
from config import *
import boto3
from datetime import timedelta
import pytz

app = Flask(__name__)
app.secret_key = "magiv"

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)

output = {}
table = 'employee'


#MAIN PAGE
@app.route("/")
def home():

    malaysian_timezone = pytz.timezone('Asia/Kuala_Lumpur')
    malaysian_time = datetime.now(malaysian_timezone)
    
    return render_template("home.html", date=malaysian_time)
    
#ADD EMPLOYEE DONE
@app.route("/addemp/",methods=['GET','POST'])
def addEmp():
    malaysian_timezone = pytz.timezone('Asia/Kuala_Lumpur')
    malaysian_time = datetime.now(malaysian_timezone)
    return render_template("AddEmp.html",date=malaysian_time)

#EMPLOYEE OUTPUT
@app.route("/addemp/results",methods=['GET','POST'])
def Emp():

    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']
    check_in =''
    insert_sql = "INSERT INTO employee (emp_id, first_name, last_name, pri_skill, location, check_in) VALUES (%s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location, check_in))
        db_conn.commit()
        emp_name = f"{first_name} {last_name}"
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = f"emp-id-{emp_id}_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)

#Attendance 
@app.route("/attendance/")
def attendance():
    malaysian_timezone = pytz.timezone('Asia/Kuala_Lumpur')
    malaysian_time = datetime.now(malaysian_timezone)
    return render_template("Attendance.html",date=malaysian_time)

#CHECK IN BUTTON
@app.route("/attendance/checkIn",methods=['GET','POST'])
def checkIn():
    malaysian_timezone = pytz.timezone('Asia/Kuala_Lumpur')
    malaysian_time = datetime.now(malaysian_timezone)
    emp_id = request.form['emp_id']

    #UPDATE STATEMENT
    update_stmt = "UPDATE employee SET check_in = %(check_in)s WHERE emp_id = %(emp_id)s"

    cursor = db_conn.cursor()

    login_time = malaysian_time
    formatted_login = login_time.strftime('%Y-%m-%d %H:%M:%S')
    print("Check in time: %s" % formatted_login)

    try:
        cursor.execute(update_stmt, {'check_in': formatted_login, 'emp_id': int(emp_id)})
        db_conn.commit()
        print(" Data Updated into MySQL")

    except Exception as e:
        return str(e)

    finally:
        cursor.close()
        
    return render_template("AttendanceOutput.html", date=malaysian_time, LoginTime=formatted_login)

from pytz import timezone
@app.route("/attendance/output", methods=['GET', 'POST'])
def checkOut():

    emp_id = request.form['emp_id']
    # SELECT STATEMENT TO GET DATA FROM MYSQL
    select_stmt = "SELECT check_in FROM employee WHERE emp_id = %(emp_id)s"
    insert_statement = "INSERT INTO attendance VALUES (%s, %s, %s, %s)"
    malaysian_timezone = timezone('Asia/Kuala_Lumpur')
    malaysian_time = datetime.now(malaysian_timezone)

    cursor = db_conn.cursor()
        
    try:
        cursor.execute(select_stmt, {'emp_id': int(emp_id)})
        login_time = cursor.fetchone()
       
        formatted_login = login_time[0]
        print(formatted_login)
        
        checkout_time = malaysian_time
        login_date = malaysian_timezone.localize(datetime.strptime(str(formatted_login), '%Y-%m-%d %H:%M:%S'))
        
        formatted_checkout = checkout_time.strftime('%Y-%m-%d %H:%M:%S')
        total_working_hours = checkout_time - login_date
        print(total_working_hours)

         
        try:
            cursor.execute(insert_statement, (int(emp_id), formatted_login, formatted_checkout, total_working_hours))
            db_conn.commit()
            print("Data inserted into MySQL")
            
            
        except Exception as e:
             return str(e)
                    
                    
    except Exception as e:
        return str(e)

    finally:
        cursor.close()
        
    return render_template("AttendanceOutput.html", date=malaysian_time, 
                            CheckOutTime=formatted_checkout, WorkingHours=total_working_hours)

   
    

#Get Employee DONE
@app.route("/getemp/")
def getEmp():
    malaysian_timezone = pytz.timezone('Asia/Kuala_Lumpur')
    malaysian_time = datetime.now(malaysian_timezone)
    
    return render_template('GetEmp.html',date=malaysian_time)


#Get Employee Results
@app.route("/getemp/results",methods=['GET','POST'])
def Employee():
    
     #Get Employee
     emp_id = request.form['emp_id']
    # SELECT STATEMENT TO GET DATA FROM MYSQL
     select_stmt = "SELECT * FROM employee WHERE emp_id = %(emp_id)s"
     malaysian_timezone = pytz.timezone('Asia/Kuala_Lumpur')
     malaysian_time = datetime.now(malaysian_timezone)

     
     cursor = db_conn.cursor()
        
     try:
         cursor.execute(select_stmt, { 'emp_id': int(emp_id) })
         # #FETCH ONLY ONE ROWS OUTPUT
         for result in cursor:
            print(result)
        

     except Exception as e:
        return str(e)
        
     finally:
        cursor.close()
    

     return render_template("GetEmpOutput.html",result=result,date=malaysian_time)


# Payroll Calculator
@app.route("/payroll/", methods=['GET', 'POST'])
def payRoll():
    malaysian_timezone = pytz.timezone('Asia/Kuala_Lumpur')
    malaysian_time = datetime.now(malaysian_timezone)
    return render_template('Payroll.html', date=malaysian_time)

# Process Payroll Calculation
@app.route("/payroll/results", methods=['GET', 'POST'])
def CalpayRoll():
    malaysian_timezone = pytz.timezone('Asia/Kuala_Lumpur')
    malaysian_time = datetime.now(malaysian_timezone)

    select_statement = "SELECT total_working_hours FROM attendance WHERE emp_id = %(emp_id)s"
    cursor = db_conn.cursor()

    if 'emp_id' in request.form and 'basic' in request.form and 'days' in request.form:
        emp_id = int(request.form.get('emp_id'))
        hourly_salary = int(request.form.get('basic'))
        workday_perweek = int(request.form.get('days'))

        try:
            cursor.execute(select_statement, {'emp_id': emp_id})
            work_hours = cursor.fetchall()
            total_seconds = 0

            for row in work_hours:
                duration = timedelta(seconds=row[0])
                hours = duration.total_seconds() / 3600
                total_seconds += hours

            working_hours = round(total_seconds, 2)

        except Exception as e:
            return str(e)

        # Calculate Payroll
        pay = round((hourly_salary * working_hours * workday_perweek), 2)
        annual = int(pay) * 12
        bonus = annual * 0.03

    else:
        print("Something is missing")
        return render_template('Payroll.html', date=malaysian_time)

    return render_template('PayrollOutput.html', date=malaysian_time, emp_id=emp_id, MonthlySalary=pay,
                           AnnualSalary=annual, WorkingHours=working_hours, Bonus=bonus)

# RMB TO CHANGE PORT NUMBER
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True) # or setting host to '0.0.0.0'
