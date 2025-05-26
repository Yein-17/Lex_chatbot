# Amazon Lex Clinic Booking Chatbot

A conversational AI chatbot built with Amazon Lex, AWS Lambda, and DynamoDB to handle clinic appointment bookings. The chatbot is deployed on a static website hosted on Amazon S3 with Kommunicate providing a modern chat interface.

## 🏗️ Architecture Overview

This project integrates several AWS services to create an interactive conversational experience:

- **Amazon Lex**: Natural language processing and conversation management
- **AWS Lambda**: Business logic and appointment handling
- **DynamoDB**: Data storage for doctor schedules and appointments
- **Amazon S3**: Static website hosting
- **Kommunicate**: Modern chat widget interface

```
User → Kommunicate Widget → Amazon Lex → AWS Lambda → DynamoDB
```

## 🚀 Features

- Natural language appointment booking
- Doctor availability checking
- Patient information collection
- Appointment confirmation system
- Modern chat interface
- Serverless architecture

## 📋 Prerequisites

- AWS Account with appropriate permissions
- Ubuntu Linux environment (or similar)
- Python 3.x with pip
- AWS CLI configured
- Kommunicate account

## 🛠️ Setup Instructions

### 1. Environment Setup

#### Install Dependencies
```bash
# Update system packages
sudo apt update
sudo apt install python3 python3-pip awscli -y

# Create Python virtual environment
python3 -m venv myenv
source myenv/bin/activate

# Install boto3
pip install boto3
```

#### Configure AWS CLI
```bash
aws configure
```
Provide your AWS credentials:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., ap-southeast-1)
- Default output format: json

### 2. Create DynamoDB Tables

#### Doctor Schedule Table
```bash
aws dynamodb create-table \
  --table-name DoctorSchedule \
  --attribute-definitions \
    AttributeName=DoctorName,AttributeType=S \
    AttributeName=Date_Time,AttributeType=S \
  --key-schema \
    AttributeName=DoctorName,KeyType=HASH \
    AttributeName=Date_Time,KeyType=RANGE \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

#### Appointments Table
```bash
aws dynamodb create-table \
  --table-name Appointments \
  --attribute-definitions \
    AttributeName=AppointmentId,AttributeType=S \
  --key-schema \
    AttributeName=AppointmentId,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

### 3. Populate Database

Create and run Python scripts to populate your DynamoDB tables:

#### Generate Doctor Schedule
```bash
# Create the script file
vim generate_schedule.py
# Add your doctor schedule generation code
python3 generate_schedule.py
```

#### Setup Appointment Handler
```bash
# Create the appointment script
vim save_appointment.py
# Add your appointment saving code
python3 save_appointment.py
```

### 4. Create Amazon Lex Chatbot

#### Basic Bot Setup
1. Go to [Amazon Lex Console](https://console.aws.amazon.com/lexv2)
2. Click "Create bot"
3. Configure:
   - **Bot name**: ClinicBookingBot
   - **IAM role**: Create new automatically
   - **Language**: English (US)
   - **Children's data**: No
   - Enable **Sentiment analysis** (optional)

#### Create Intent: BookingAppointmentIntent

**Sample Utterances:**
- "I want to book an appointment"
- "Book a doctor"
- "I need to see {DoctorName}"
- "Book me with Dr. {DoctorName} on {Date} at {Time}"

#### Custom Slot Types

1. **DoctorNameType**: Custom slot with doctor names
   - Dr. Sarah Jones
   - Dr. Sophia Lee
   - Dr. David Park

2. **NameType**: Free text slot for patient names

#### Required Slots Configuration

| Slot Name | Slot Type | Prompt |
|-----------|-----------|---------|
| DoctorName | DoctorNameType | "Which doctor would you like to see?" |
| Date | AMAZON.Date | "What date would you prefer?" |
| Time | AMAZON.Time | "What time works for you?" |
| PatientName | NameType | "What's your full name?" |
| PhoneNumber | AMAZON.PhoneNumber | "What's your phone number?" |
| Email | AMAZON.EmailAddress | "What's your email address?" |

#### Confirmation Setup
- **Confirmation prompt**: "If everything is correct, I will proceed with booking confirmation."
- **Decline response**: "Okay! I will cancel the booking."

### 5. Create AWS Lambda Function

#### Lambda Configuration
1. Go to AWS Lambda Console
2. Create function:
   - **Function name**: BookAppointmentHandler
   - **Runtime**: Python 3.12
   - **Permissions**: Create new role with basic Lambda permissions

#### Add DynamoDB Permissions
1. Go to IAM Console → Roles
2. Find your Lambda role
3. Attach `AmazonDynamoDBFullAccess` policy

#### Connect Lambda to Lex
1. In your Lex bot, go to BookingAppointmentIntent
2. Under Fulfillment, select "AWS Lambda function"
3. Choose your BookAppointmentHandler function
4. Grant invoke permissions when prompted

### 6. Integrate with Kommunicate

#### Setup Kommunicate
1. Create account at [Kommunicate.io](https://www.kommunicate.io/)
2. Navigate to Bot Integrations → Amazon Lex
3. Configure integration:
   - **Bot Name**: ClinicBookingBot
   - **Bot Alias**: live
   - **AWS Credentials**: Create IAM user with AmazonLexFullAccess
   - **Region**: Your Lex bot region

#### Get Embed Code
1. Go to Settings → Install → Website tab
2. Copy the JavaScript embed code
3. Add to your website's HTML

### 7. Deploy Static Website on S3

#### Create S3 Bucket
```bash
# Create bucket (replace with your bucket name)
aws s3 mb s3://your-clinic-chatbot-site --region your-region
```

#### Configure Bucket for Website Hosting
1. Go to S3 Console
2. Select your bucket
3. Properties → Static website hosting → Enable
4. Set index document: `index.html`

#### Set Bucket Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::your-clinic-chatbot-site/*"
    }
  ]
}
```

## 🧪 Testing

1. Open your S3 static website URL
2. Look for the Kommunicate chat widget (bottom right)
3. Test with: "I want to book an appointment with Dr. Sarah Jones"
4. Complete the conversation flow
5. Verify appointment is saved in DynamoDB

## 📁 Project Structure

```
clinic-booking-chatbot/
├── scripts/
│   ├── generate_schedule.py
│   └── save_appointment.py
├── lambda/
│   └── BookAppointmentHandler.py
├── website/
│   └── index.html
└── README.md
```

## 🔧 Configuration Files

### AWS CLI Configuration
Location: `~/.aws/credentials`

### Required IAM Policies
- `AmazonLexFullAccess`
- `AmazonDynamoDBFullAccess`
- `AmazonS3FullAccess`
- `AWSLambdaBasicExecutionRole`

## 🚦 Common Issues

### Lambda Function Issues
- Ensure proper IAM permissions for DynamoDB access
- Check Lambda function timeout settings
- Verify Lex integration permissions

### DynamoDB Issues
- Confirm table names match exactly
- Check provisioned capacity settings
- Verify AWS region consistency

### Website Issues
- Ensure S3 bucket policy allows public read access
- Check static website hosting configuration
- Verify Kommunicate embed code placement

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For issues and questions:
- Create an issue in this repository
- Check AWS documentation for service-specific problems
- Review Kommunicate documentation for integration issues

## 🔗 Useful Links

- [Amazon Lex Documentation](https://docs.aws.amazon.com/lex/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [Kommunicate Documentation](https://docs.kommunicate.io/)

---

**Note**: Remember to deactivate your Python virtual environment when done:
```bash
deactivate
```
