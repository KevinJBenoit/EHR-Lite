from flask import Flask, render_template
from flask import request, redirect, url_for
from flask import session
from db_connector.db_connector import connect_to_database, execute_query

import sys
cache= {}
#create the web application
webapp = Flask(__name__)

#provide a route where requests on the web application can be addressed
@webapp.route('/hello')
#provide a view (fancy name for a function) which responds to any requests on this route
def hello():
    return "Hello World!"



@webapp.route('/', methods=['GET', 'POST'])
def home():
    #establish sessions to prevent keyErrors
    session['visitData'] = 0
    session['patientData'] = 0
    session['providerUpdateVisitID'] = 0
    session['providerUpdateVisitObj'] = 0
    session['patient_mrn'] = 0
    session['providerPatientObj'] = 0

    if request.method =='POST':
        print("REQUEST.FORM: ", request.form)

        #if routing to providers
        if request.form['userType'] == "providers":
            print("PRINT: userTYPE:")
            print(request.form['userType'], file=sys.stdout)
            return redirect(url_for('providers')) #pass id number here for redirect

        #if routing to patient
        elif request.form['userType'] =="patient":
            print("PRINT: userTYPE: ")
            print(request.form['userType'], file=sys.stdout)
            return redirect(url_for('patient')) #pass id number here for redirect
        #if routing to admin
        elif request.form['userType'] =="admin":
            print("PRINT: userTYPE: ")
            print(request.form['userType'], file=sys.stdout)
            return redirect(url_for('admin')) #pass id number here for redirect

    return render_template('home.html')



@webapp.route('/patient')
def patient():
    return render_template('patient.html')



"""
Webapp route for handling frontend <--> backend logic of the providers page
"""
@webapp.route('/providers', methods=['GET', 'POST'])
def providers():
    #setup for connecting to our database
    db_connection = connect_to_database()


    try:
        session['visitData']
        session['patientData']
        session['providerUpdateVisitID']
        session['providerUpdateVisitObj']
        session['patient_mrn']
        session['providerPatientObj']
        session['diagnosisOptions']
    except KeyError as error:
        session['patient_mrn'] = 0
        session['providerPatientObj'] = 0
        session['visitData'] = 0
        session['patientData'] = 0
        session['providerUpdateVisitID'] = 0
        session['providerUpdateVisitObj'] = 0
        session['diagnosisOptions'] = 0
        print("caught keyerror", error)

    if session['diagnosisOptions']:
        diagnosisOptions = session['diagnosisOptions']
    else:
        query = "SELECT diagnosisCode FROM diagnoses"
        result = execute_query(db_connection, query)
        row_headers = [x[0] for x in result.description]
        row_variables = result.fetchall()
        diagnosisOptions = []
        for row_string in row_variables:
            diagnosisOptions.append(row_string[0])

    if session['patient_mrn']:
        patient_mrn = session['patient_mrn']
    else:
        patient_mrn = -1

    if session['providerPatientObj']:
        providerPatientObj = session['providerPatientObj']
    else:
        providerPatientObj = {}

    if session['visitData']:
        visitData = session['visitData']
    else:
        visitData = {}

    if session['patientData']:
        patientData = session['patientData']
    else:
        patientData = {}

    if session['providerUpdateVisitID'] :
        providerUpdateVisitID = session['providerUpdateVisitID']
    else:
        providerUpdateVisitID = -1

    if session['providerUpdateVisitObj']:
        providerUpdateVisitObj = session['providerUpdateVisitObj']
    else:
        providerUpdateVisitObj = {}


    #Handler for parsing requests made from submission of one of the forms
    if request.method =='POST':
        #Accessing Patient Information in Providers Portal
        #New Patient = providerNewPatient
        if 'providerNewPatient' in request.form:
            print("ADDING PATIENT INFO")

            patient_fname = request.form['newPatientFirstName']
            patient_lname = request.form['newPatientLastName']
            patient_birthdate = request.form['newPatientBirthdate']
            patient_pcp = request.form['primaryCarePhysician']
            patient_pharamcy = request.form['patientPreferredPharmacy']

            query = """INSERT INTO patients (fname, lname, birthdate, preferredPharmacy, primaryCarePhysician)
                            VALUES ('{}', '{}', '{}', '{}', {});""".format(patient_fname, patient_lname, patient_birthdate, patient_pharamcy,  patient_pcp)

            execute_query(db_connection, query)

        #Discharge Patient = providerDischargePatient
        elif 'providerDischargePatient' in request.form:
            print("DELETEING PATIENT INFO")
            print("patient_mrn: ", request.form['medicalRecordNumber'])
            patient_mrn = request.form['medicalRecordNumber']

            query = """DELETE FROM patients WHERE medicalRecordNumber = {};""".format(patient_mrn)

            execute_query(db_connection, query)

        #Enter ID of Patient to update = providerLookupPatient
        elif 'providerLookupPatient' in request.form:
            print("LOOKUP PATIENT INFO")

            #save patient id for update query form
            patient_mrn = request.form['patientID']
            session['patient_mrn'] = patient_mrn

            #this query was not in dataManipulation.sql
            query = """SELECT medicalRecordNumber, fname, lname, birthdate, primaryCarePhysician, preferredPharmacy FROM patients
                            WHERE medicalRecordNumber = {};""".format(patient_mrn)
            result = execute_query(db_connection, query)

            row_headers = [x[0] for x in result.description]
            row_variables = result.fetchall() #be careful, this pop's the data as well
            json_data = []
            for row_string in row_variables:
                json_data.append(dict(zip(row_headers, row_string)))

            providerPatientObj = json_data
            session['providerPatientObj'] = providerPatientObj

        #Update Patient Information = providerUpdatePatient
        elif 'providerUpdatePatient' in request.form:
            print("UPDATING PATIENT INFO")

            patient_mrn = session['patient_mrn']

            patient_fname = request.form['fname']
            patient_lname = request.form['lname']
            patient_birthdate = request.form['birthdate']
            patient_pcp_num = request.form['primaryCarePhysicianNum']
            patient_pharamcy = request.form['preferredPharmacy']

            query = """UPDATE patients SET fname = '{}', lname = '{}', birthdate = '{}', primaryCarePhysician = {}, preferredPharmacy = '{}'
                            WHERE medicalRecordNumber = {};""".format(patient_fname, patient_lname, patient_birthdate, patient_pcp_num, patient_pharamcy, patient_mrn)

            execute_query(db_connection, query)

            #clear the Update Patient Fields
            session['providerPatientObj'] = {}
            providerPatientObj = {}

        # Access Visit Information in Providers Portal
        #New Visit = providersNewVisit
        elif 'providersNewVisit' in request.form:
            print("ADDING NEW VISIT")

            visit_date = request.form['visitDate']
            chief_complaint = request.form['chiefComplaint']
            diagnosis_code = request.form['diagnosisCode']
            procedure_code = request.form['procedureCode']
            patient_mrn = request.form['patientID']
            clinic_id = request.form['clinicID']
            provider_id = request.form['providerID']
            notes_string = request.form['providerNotes']

            query = """INSERT INTO visits (visitDate, chiefComplaint, diagnosisCode, procedureCode, patient, provider, clinic, providerNotes)
                            VALUES ('{}', '{}', '{}', '{}', {}, {}, {}, '{}');
                            """.format(visit_date, chief_complaint, diagnosis_code, procedure_code, patient_mrn, clinic_id, provider_id, notes_string)
            execute_query(db_connection, query)

        #Enter ID of Visit to update "Enter Account Number" = providersVisitLookup
        elif 'providersVisitLookup' in request.form:
            print("LOOKING UP VISIT BEFORE UPDATE")

            #save visit id for update query form
            visit_id = request.form['accountNumber']
            session['providerUpdateVisitID'] = visit_id

            query = """SELECT visitDate, chiefComplaint, diagnosisCode, procedureCode, patient, clinic, provider, providerNotes  FROM visits
                        WHERE accountNumber = {};""".format(visit_id)
            result = execute_query(db_connection, query)

            row_headers = [x[0] for x in result.description]
            row_variables = result.fetchall() #be careful, this pop's the data as well
            json_data = []
            for row_string in row_variables:
                json_data.append(dict(zip(row_headers, row_string)))

            providerUpdateVisitObj = json_data
            session['providerUpdateVisitObj'] = providerUpdateVisitObj

        #Update Visit Information = providersUpdateVisit
        elif 'providersUpdateVisit' in request.form:
            print("UPDATING NEW VISIT")
            account_number = session['providerUpdateVisitID']
            sqlData = []
            visit_date = request.form['visitDate']
            chief_complaint = request.form['chiefComplaint']
            diagnosis_code = request.form['diagnosisCode']
            procedure_code = request.form['procedureCode']
            patient_mrn = request.form['patientID']
            clinic_id = request.form['clinicID']
            provider_id = request.form['providerID']
            notes_string = request.form['providerNotes']

            query = """UPDATE visits SET visitDate = '{}', chiefComplaint = '{}', diagnosisCode = '{}', procedureCode = '{}', patient = {}, clinic = {}, provider = {}, providerNotes = '{}'
                        WHERE accountNumber = {};""".format(visit_date, chief_complaint, diagnosis_code, procedure_code, patient_mrn, clinic_id, provider_id, notes_string, account_number)
            execute_query(db_connection, query)

            #clear the Update Visit Fields
            session['providerUpdateVisitObj'] = {}
            providerUpdateVisitObj = {}

        #Delete Visit = providersDeleteVisit
        elif 'providersDeleteVisit' in request.form:
            print("DELETING VISIT")
            visit_id = request.form['accountNumber']

            query = """DELETE FROM visits WHERE accountNumber = {};""".format(visit_id)
            execute_query(db_connection, query)

        #View Visists by Date = viewVisits
        elif 'providersViewVisits' in request.form:
            print("VIEWING VISITS")
            visit_date = request.form['visitDate']

            #modified this SQL from dataManipulation.sql
            query = """SELECT visits.accountNumber, CONCAT(patients.fname, ' ', patients.lname) AS patient, visits.chiefComplaint, clinics.clinicName, diagnoses.diagnosisName, procedures.procedureName, CONCAT(providers.fname, ' ', providers.lname) AS 'PCP', visits.providerNotes FROM visits
                        JOIN patients ON patients.medicalRecordNumber = visits.patient
                        JOIN clinics  ON clinics.clinicID = visits.clinic
                        LEFT JOIN diagnoses ON diagnoses.diagnosisCode = visits.diagnosisCode
                        JOIN procedures ON procedures.procedureCode = visits.procedureCode
                        JOIN providers ON providers.providerID = visits.provider
                        WHERE visits.visitDate = '{}';""".format(visit_date)
            result = execute_query(db_connection, query)

            row_headers = [x[0] for x in result.description]
            row_variables = result.fetchall() #be careful, this pop's the data as well
            json_data = []
            for row_string in row_variables:
                json_data.append(dict(zip(row_headers, row_string)))
            visitData = json_data
            session['visitData'] = visitData

        #View Patients of Provider = viewProviderPatients
        elif 'viewProviderPatients' in request.form:
            print("VIEWING PATIENTS")

            provider_id = request.form['providerID']

            query = """SELECT patients.medicalRecordNumber, patients.fname, patients.lname, patients.birthdate, CONCAT(providers.fname, ' ', providers.lname) AS 'PCP', patients.preferredPharmacy FROM patients
                            JOIN providers ON providers.providerID = patients.primaryCarePhysician
                            WHERE providers.providerID = {};""".format(provider_id)
            result = execute_query(db_connection, query)

            row_headers = [x[0] for x in result.description]
            row_variables = result.fetchall() #be careful, this pop's the data as well
            json_data = []
            for row_string in row_variables:
                json_data.append(dict(zip(row_headers, row_string)))
            patientData = json_data
            session['patientData'] = patientData
            #return render_template('providers.html', patientData=patientData)

        return render_template('providers.html', diagnosisOptions=diagnosisOptions, patientData=patientData, visitData = visitData, providerUpdateVisitObj = providerUpdateVisitObj, providerPatientObj=providerPatientObj)

    return render_template('providers.html')




@webapp.route('/admin')
def admin():
    #setup for connecting to our database
    db_connection = connect_to_database()

    return render_template('admin.html')

webapp.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'