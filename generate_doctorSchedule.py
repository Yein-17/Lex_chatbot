import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

# Initialize DynamoDB table resource
dynamodb = boto3.resource('dynamodb')
doctor_table = dynamodb.Table('DoctorSchedule')

# Weekly doctor schedule (0=Monday, ..., 6=Sunday)
doctor_weekdays = {
    'Dr. Sarah Jones': [0, 1, 2, 3, 4],      # Mon–Fri
    'Dr. Sophia Lee': [0, 1, 2, 3],          # Mon–Thu
    'Dr. David Park': [1, 2, 3, 4],          # Tue–Fri
}

# Timeslots available each day
available_times = ['09:00', '10:00', '11:00', '12:00']


def clear_schedule():
    """Scan and delete all items from DoctorSchedule table"""
    try:
        print("🧹 Clearing old schedule...")
        scan = doctor_table.scan()
        with doctor_table.batch_writer() as batch:
            for item in scan['Items']:
                batch.delete_item(
                    Key={
                        'DoctorName': item['DoctorName'],
                        'Date_Time': item['Date_Time']
                    }
                )
        print("✅ Old schedule cleared.")
    except ClientError as e:
        print(f"❌ Error clearing schedule: {e.response['Error']['Message']}")


def generate_schedule():
    """Generate and insert doctor availability for May 2025"""
    try:
        print("🗓️ Generating new schedule for May 2025...")
        start_date = datetime(2025, 5, 1)
        end_date = datetime(2025, 5, 31)

        for doctor_name, working_days in doctor_weekdays.items():
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() in working_days:
                    date_str = current_date.strftime('%Y-%m-%d')
                    for time in available_times:
                        date_time = f"{date_str}_{time}"
                        doctor_table.put_item(
                            Item={
                                'DoctorName': doctor_name,
                                'Date_Time': date_time,
                                'Status': 'available'
                            }
                        )
                current_date += timedelta(days=1)

        print("✅ New doctor schedule for May 2025 has been generated.")
    except ClientError as e:
        print(f"❌ Error generating schedule: {e.response['Error']['Message']}")


# Run both steps
if __name__ == "__main__":
    clear_schedule()
    generate_schedule()