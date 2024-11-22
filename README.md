# Healthcare Appointment Management System (Work in Progress)

## Project Status
This project is currently under active development. Core features have been implemented, and we are working on expanding functionality. This is an independent project, not a group effort.

## Description
This is a Django-based healthcare appointment management system that allows patients to book appointments with doctors. It includes advanced user authentication, appointment scheduling, and doctor management. The project is continuously evolving, with more advanced features planned for future implementation.

## Current Features
- User Management:
  - Patient and Doctor registration and authentication
    - Traditional username/password registration
    - Google Sign-Up integration for easy access
    - Email verification for enhanced security
  - User profile management (edit profile, change password)
  - Admin user management with distinction between social and traditional sign-ups
- Appointment System:
  - Create, view, update, and delete appointments
  - Appointment status tracking (Scheduled, Completed, Cancelled)
  - Doctor availability management
- Doctor Management:
  - Doctor registration with specialization
  - Doctor profile management
- Admin Interface:
  - Manage users, doctors, and appointments
  - Distinguish between users registered via social auth and traditional methods

## Planned Features
- Patient Payment System
- Drug Booking and Ordering System
- Dispatch Management (Dispatch Company Registration)
- Real-Time Chat Functionality
- AI Chatbot Integration
- Enhanced Admin Dashboard
- User Feedback and Rating System
- Notifications System

## Technologies Used
- Django
- Django Rest Framework
- SQLite (default database)
- Google OAuth for social authentication

## Authentication Files
The following files are crucial for the authentication system:
- `client_secret.json`: Contains Google OAuth client secrets
- `token.json`: Stores authentication tokens
- `test_set_role.py`: Tests role assignment functionality
- `scripts/get_google_token.py`: Script to obtain Google authentication tokens

## Installation

1. Clone the repository:

git clone [https://github.com/your-officialmelvinp/healthcare-app.git]

cd healthcare-app


2. Create a virtual environment and activate it:
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`


3. Install the required packages:
pip install -r requirements.txt

5. Create a superuser:

python manage.py createsuperuser

#####
## Usage

1. Start the development server:

python manage.py runserver


2. Access the admin interface at `http://localhost:8000/admin/` to manage users and appointments.

3. Use the API endpoints to interact with the system programmatically. Main endpoints include:
- `/api/register/`: User management
- `/api/appointments/`: Appointment management
 `/api/google-signin/`: google signin
 `/api/token/`: user login


## Testing

Run the tests using:

python manage.py test

############




## API Documentation

(API documentation will be added as the project progresses)

## Contributing

As this project is still in development, contribution guidelines will be established in the future. For now, please feel free to open issues for bugs or feature suggestions.

## License

This project is currently not licensed for public use or distribution as it's still in development.

## Acknowledgments

- Special thanks to the Django and Django Rest Framework communities for their excellent documentation and tools.

## Project Roadmap

### Completed Features
- [x] User Registration and Authentication
- [x] User Profile Management
- [x] Doctor Registration and Management
- [x] Basic Appointment System
- [x] Admin Interface for User and Appointment Management

### Upcoming Features
- [ ] Patient Payment System
- [ ] Drug Booking and Ordering System
- [ ] Dispatch Management
- [ ] Real-Time Chat Functionality
- [ ] AI Chatbot Integration
- [ ] Enhanced Admin Dashboard
- [ ] User Feedback and Rating System
- [ ] Notifications System

(For a detailed breakdown of upcoming features, please refer to the project documentation)
