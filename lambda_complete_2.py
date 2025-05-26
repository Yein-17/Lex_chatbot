import boto3
import logging
from botocore.exceptions import ClientError

# Initialize DynamoDB resources
dynamodb = boto3.resource('dynamodb')
schedule_table = dynamodb.Table('DoctorSchedule')
appointments_table = dynamodb.Table('Appointments')
id_counter_table = dynamodb.Table('IdCounters')

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_next_sequence():
    """Generate the next appointment ID using a counter"""
    response = id_counter_table.update_item(
        Key={'counter_name': 'appointment_id'},
        UpdateExpression='SET current_value = if_not_exists(current_value, :start) + :incr',
        ExpressionAttributeValues={
            ':incr': 1,
            ':start': 1000000
        },
        ReturnValues='UPDATED_NEW'
    )
    return str(response['Attributes']['current_value'])[-7:]

def get_slot_value(slots, slot_name):
    """Helper function to extract interpreted slot value"""
    slot = slots.get(slot_name)
    if slot and 'value' in slot and 'interpretedValue' in slot['value']:
        return slot['value']['interpretedValue']
    return None

def get_available_times(doctor, date):
    """Query available time slots for a doctor on a specific date"""
    response = schedule_table.scan(
        FilterExpression='DoctorName = :doc AND begins_with(Date_Time, :dt) AND #s = :status',
        ExpressionAttributeNames={'#s': 'Status'},
        ExpressionAttributeValues={
            ':doc': doctor,
            ':dt': date,
            ':status': 'available'
        }
    )
    return [item['Date_Time'].split('_')[1] for item in response['Items']]

def lambda_handler(event, context):
    try:
        intent = event['sessionState']['intent']
        slots = intent['slots']
        invocation_source = event['invocationSource']
        confirmation_state = intent.get('confirmationState', '')

        # List of valid doctors (must match your Lex slot values)
        VALID_DOCTORS = ['Dr. Sarah Jones', 'Dr. Sophia Lee', 'Dr. David Park']
        
        doctor = get_slot_value(slots, 'DoctorName')
        
        # Validate doctor name
        if doctor:
            # Case-insensitive comparison
            if not any(d.lower() == doctor.lower() for d in VALID_DOCTORS):
                return {
                    "sessionState": {
                        "dialogAction": {
                            "type": "ElicitSlot",
                            "slotToElicit": "DoctorName"
                        },
                        "intent": intent
                    },
                    "messages": [{
                        "contentType": "PlainText",
                        "content": "Please choose from our available doctors:\n- Dr. Sarah Jones\n- Dr. Sophia Lee\n- Dr. David Park"
                    }]
                }
            # Normalize to exact case from VALID_DOCTORS
            doctor = next(d for d in VALID_DOCTORS if d.lower() == doctor.lower())
            slots['DoctorName']['value']['interpretedValue'] = doctor

        date = get_slot_value(slots, 'Date')
        time = get_slot_value(slots, 'Time')
        name = get_slot_value(slots, 'Name')
        phone = get_slot_value(slots, 'Phone')
        confirmation = get_slot_value(slots, 'Confirmation')

        # Step 1: Check available time slots if doctor and date are provided but time isn't
        if doctor and date and not time:
            available_times = get_available_times(doctor, date)
            
            if not available_times:
                return {
                    "sessionState": {
                        "dialogAction": {
                            "type": "ElicitSlot", 
                            "slotToElicit": "Date"
                        },
                        "intent": {**intent, "slots": {**slots, "Date": None}}
                    },
                    "messages": [{
                        "contentType": "PlainText",
                        "content": f"Sorry, {doctor} has no available slots on {date}. Please choose another date."
                    }]
                }
            else:
                return {
                    "sessionState": {
                        "dialogAction": {
                            "type": "ElicitSlot",
                            "slotToElicit": "Time"
                        },
                        "intent": intent
                    },
                    "messages": [{
                        "contentType": "PlainText",
                        "content": f"{doctor} is available on {date} at: {', '.join(available_times)}. Please choose a time."
                    }]
                }

        # Step 2: Validate time slot if provided
        if doctor and date and time:
            available_times = get_available_times(doctor, date)
            
            # Normalize time format
            normalized_time = time.strip().upper().replace(' ', '').replace('.', '')
            normalized_time = ''.join([c for c in normalized_time if c.isdigit() or c == ':'])
            
            # Check if time is available
            if time not in available_times:
                return {
                    "sessionState": {
                        "dialogAction": {
                            "type": "ElicitSlot",
                            "slotToElicit": "Time"
                        },
                        "intent": intent
                    },
                    "messages": [{
                        "contentType": "PlainText",
                        "content": f"Sorry, {time} is not available. {doctor} is available on {date} at: {', '.join(available_times)}. Please choose one of these times."
                    }]
                }
            
            # Step 3: Ask for Name and Phone if missing
            if not name:
                return {
                    "sessionState": {
                        "dialogAction": {
                            "type": "ElicitSlot",
                            "slotToElicit": "Name"
                        },
                        "intent": intent
                    },
                    "messages": [{
                        "contentType": "PlainText",
                        "content": "May I know your name?"
                    }]
                }
            if not phone:
                return {
                    "sessionState": {
                        "dialogAction": {
                            "type": "ElicitSlot",
                            "slotToElicit": "Phone"
                        },
                        "intent": intent
                    },
                    "messages": [{
                        "contentType": "PlainText",
                        "content": "Could you please provide your phone number?"
                    }]
                }

        # Step 4: Ask user to confirm details when all slots are filled
        if doctor and date and time and name and phone and not confirmation:
            confirm_msg = f"Please confirm your booking details:\nDoctor: {doctor}\nDate: {date}\nTime: {time}\nName: {name}\nPhone: {phone}\nIs this correct?"
            return {
                "sessionState": {
                    "dialogAction": {
                        "type": "ElicitSlot",
                        "slotToElicit": "Confirmation"
                    },
                    "intent": intent
                },
                "messages": [{
                    "contentType": "PlainText",
                    "content": confirm_msg
                }]
            }

        # Step 5: Handle confirmation response
        if confirmation:
            if confirmation.lower() == 'no':
                # FIXED: Reset all slots but keep the current intent
                # Don't try to set a new intentName in dialogAction
                return {
                    "sessionState": {
                        "dialogAction": {
                            "type": "ElicitSlot",
                            "slotToElicit": "DoctorName"
                        },
                        "intent": {
                            "name": intent['name'],  # Keep the current intent name
                            "slots": {
                                "DoctorName": None,
                                "Date": None,
                                "Time": None,
                                "Name": None,
                                "Phone": None,
                                "Confirmation": None
                            },
                            "state": "InProgress"
                        }
                    },
                    "messages": [{
                        "contentType": "PlainText",
                        "content": "Okay, let's start over. Which doctor would you like to book an appointment with?"
                    }]
                }
            elif confirmation.lower() == 'yes':
                return {
                    "sessionState": {
                        "dialogAction": {"type": "Delegate"},
                        "intent": intent
                    }
                }

        # Step 6: Handle built-in confirmation denial
        if confirmation_state == 'Denied':
            # FIXED: Reset all slots but keep the current intent
            return {
                "sessionState": {
                    "dialogAction": {
                        "type": "ElicitSlot",
                        "slotToElicit": "DoctorName"
                    },
                    "intent": {
                        "name": intent['name'],  # Keep the current intent name
                        "slots": {
                            "DoctorName": None,
                            "Date": None,
                            "Time": None,
                            "Name": None,
                            "Phone": None,
                            "Confirmation": None
                        },
                        "state": "InProgress"
                    }
                },
                "messages": [{
                    "contentType": "PlainText",
                    "content": "Your booking was canceled. Which doctor would you like to book with?"
                }]
            }

        # Step 7: Final fulfillment
        if invocation_source == 'FulfillmentCodeHook' and confirmation_state == 'Confirmed':
            datetime_key = f"{date}_{time}"
            
            try:
                # Mark slot as booked
                schedule_table.update_item(
                    Key={'DoctorName': doctor, 'Date_Time': datetime_key},
                    UpdateExpression="SET #status = :status",
                    ConditionExpression="attribute_exists(DoctorName) AND attribute_exists(Date_Time) AND #status = :available",
                    ExpressionAttributeNames={'#status': 'Status'},
                    ExpressionAttributeValues={
                        ':status': 'booked',
                        ':available': 'available'
                    }
                )
                
                # Create appointment record
                appointment_id = get_next_sequence()
                appointments_table.put_item(
                    Item={
                        'AppointmentId': appointment_id,
                        'DoctorName': doctor,
                        'Date': date,
                        'Time': time,
                        'Name': name,
                        'Phone': phone,
                        'Status': 'confirmed'
                    }
                )

                return {
                    "sessionState": {
                        "dialogAction": {"type": "Close"},
                        "intent": {
                            "name": intent['name'],
                            "slots": intent['slots'],
                            "state": "Fulfilled"
                        }
                    },
                    "messages": [{
                        "contentType": "PlainText",
                        "content": f"✅ Appointment confirmed!\nID: {appointment_id}\nDoctor: {doctor}\nDate: {date}\nTime: {time}"
                    }]
                }
                
            except ClientError as e:
                logger.error(f"Booking failed: {e}")
                return {
                    "sessionState": {
                        "dialogAction": {"type": "Close"},
                        "intent": intent
                    },
                    "messages": [{
                        "contentType": "PlainText",
                        "content": "❌ Sorry, that time slot was just booked by someone else. Please try another time."
                    }]
                }

        # Default fallback - delegate to Lex
        return {
            "sessionState": {
                "dialogAction": {"type": "Delegate"},
                "intent": intent
            }
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            "sessionState": {
                "dialogAction": {"type": "Close"},
                "intent": event.get('sessionState', {}).get('intent', {})
            },
            "messages": [{
                "contentType": "PlainText",
                "content": "Something went wrong. Please try again later."
            }]
        }