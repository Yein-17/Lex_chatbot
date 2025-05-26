import boto3
from uuid import uuid4

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
appointments_table = dynamodb.Table('Appointments')

def add_appointment(doctor_name, date_time, patient_name, phone_number, service):
    appointment_id = str(uuid4())  # Unique ID for each appointment

    # Insert appointment details into the Appointments table
    appointments_table.put_item(
        Item={
            'AppointmentId': appointment_id,
            'DoctorName': doctor_name,
            'Date_Time': date_time,
            'PatientName': patient_name,
            'PhoneNumber': phone_number,
            'Service': service
        }
    )

    print(f"Appointment booked for {patient_name} with {doctor_name} at {date_time}")