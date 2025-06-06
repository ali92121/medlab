import React from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { PatientCreationPayload } from '../../services/patientService'; // Assuming path is correct

// Define the form data structure based on PatientCreationPayload
type PatientFormData = PatientCreationPayload;

interface PatientRegistrationFormProps {
  onSubmit: SubmitHandler<PatientFormData>;
  defaultValues?: Partial<PatientFormData> & { id?: number }; // For editing or pre-filling, include id
  isLoading?: boolean;
}

const PatientRegistrationForm: React.FC<PatientRegistrationFormProps> = ({ onSubmit, defaultValues, isLoading }) => {
  const { register, handleSubmit, formState: { errors } } = useForm<PatientFormData>({
    defaultValues: defaultValues || {
      first_name: '',
      last_name: '',
      psychiatry_id: '',
      date_of_birth: '', // Should be YYYY-MM-DD
      gender: '',
      phone_number: '',
      email: '',
      address: {
        address_line1: '',
        city: '',
        state_province: '',
        postal_code: '',
        country: '',
      },
      emergency_contact: {
        name: '',
        phone: '',
        relationship: '',
      },
      primary_care_physician: '',
    }
  });

  const formSectionStyle: React.CSSProperties = {
    marginBottom: '2rem',
    padding: '1.5rem',
    border: '1px solid #eee',
    borderRadius: '8px',
    backgroundColor: '#f9f9f9',
  };

  const fieldStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    marginBottom: '1rem',
  };

  const labelStyle: React.CSSProperties = {
    marginBottom: '0.5rem',
    fontWeight: 'bold',
  };

  const inputStyle: React.CSSProperties = {
    padding: '0.75rem',
    border: '1px solid #ccc',
    borderRadius: '4px',
    fontSize: '1rem',
  };

  const errorStyle: React.CSSProperties = {
    color: 'red',
    fontSize: '0.875rem',
    marginTop: '0.25rem',
  };

  const buttonStyle: React.CSSProperties = {
    padding: '0.75rem 1.5rem',
    fontSize: '1rem',
    color: '#fff',
    backgroundColor: '#007bff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    opacity: isLoading ? 0.7 : 1,
  };


  return (
    <form onSubmit={handleSubmit(onSubmit)} style={{ maxWidth: '800px', margin: '0 auto' }}>
      {/* Patient Identification Section */}
      <section style={formSectionStyle}>
        <h2>Patient Identification</h2>
        <div style={fieldStyle}>
          <label htmlFor="psychiatry_id" style={labelStyle}>Psychiatry ID (Optional)</label>
          <input id="psychiatry_id" {...register('psychiatry_id')} style={inputStyle} />
        </div>
        <div style={fieldStyle}>
          <label htmlFor="first_name" style={labelStyle}>First Name*</label>
          <input id="first_name" {...register('first_name', { required: 'First name is required' })} style={inputStyle} />
          {errors.first_name && <p style={errorStyle}>{errors.first_name.message}</p>}
        </div>
        <div style={fieldStyle}>
          <label htmlFor="last_name" style={labelStyle}>Last Name*</label>
          <input id="last_name" {...register('last_name', { required: 'Last name is required' })} style={inputStyle} />
          {errors.last_name && <p style={errorStyle}>{errors.last_name.message}</p>}
        </div>
      </section>

      {/* Demographics Section */}
      <section style={formSectionStyle}>
        <h2>Demographics</h2>
        <div style={fieldStyle}>
          <label htmlFor="date_of_birth" style={labelStyle}>Date of Birth</label>
          <input id="date_of_birth" type="date" {...register('date_of_birth')} style={inputStyle} />
          {errors.date_of_birth && <p style={errorStyle}>{errors.date_of_birth.message}</p>}
        </div>
        <div style={fieldStyle}>
          <label htmlFor="gender" style={labelStyle}>Gender</label>
          <select id="gender" {...register('gender')} style={inputStyle}>
            <option value="">Select Gender</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Other">Other</option>
            <option value="Prefer not to say">Prefer not to say</option>
          </select>
        </div>
      </section>

      {/* Contact Information Section */}
      <section style={formSectionStyle}>
        <h2>Contact Information</h2>
        <div style={fieldStyle}>
          <label htmlFor="phone_number" style={labelStyle}>Phone Number</label>
          <input id="phone_number" type="tel" {...register('phone_number')} style={inputStyle} />
        </div>
        <div style={fieldStyle}>
          <label htmlFor="email" style={labelStyle}>Email</label>
          <input id="email" type="email" {...register('email', { pattern: { value: /^\S+@\S+$/i, message: "Invalid email address" }})} style={inputStyle} />
          {errors.email && <p style={errorStyle}>{errors.email.message}</p>}
        </div>
        <div style={fieldStyle}>
          <label htmlFor="address_line1" style={labelStyle}>Address Line 1</label>
          <input id="address_line1" {...register('address.address_line1')} style={inputStyle} />
        </div>
        <div style={fieldStyle}>
          <label htmlFor="city" style={labelStyle}>City</label>
          <input id="city" {...register('address.city')} style={inputStyle} />
        </div>
        <div style={fieldStyle}>
          <label htmlFor="state_province" style={labelStyle}>State/Province</label>
          <input id="state_province" {...register('address.state_province')} style={inputStyle} />
        </div>
        <div style={fieldStyle}>
          <label htmlFor="postal_code" style={labelStyle}>Postal Code</label>
          <input id="postal_code" {...register('address.postal_code')} style={inputStyle} />
        </div>
        <div style={fieldStyle}>
          <label htmlFor="country" style={labelStyle}>Country</label>
          <input id="country" {...register('address.country')} style={inputStyle} />
        </div>
      </section>

      {/* Emergency Contact Section */}
      <section style={formSectionStyle}>
        <h2>Emergency Contact</h2>
        <div style={fieldStyle}>
          <label htmlFor="emergency_contact_name" style={labelStyle}>Name</label>
          <input id="emergency_contact_name" {...register('emergency_contact.name')} style={inputStyle} />
        </div>
        <div style={fieldStyle}>
          <label htmlFor="emergency_contact_phone" style={labelStyle}>Phone</label>
          <input id="emergency_contact_phone" type="tel" {...register('emergency_contact.phone')} style={inputStyle} />
        </div>
        <div style={fieldStyle}>
          <label htmlFor="emergency_contact_relationship" style={labelStyle}>Relationship</label>
          <input id="emergency_contact_relationship" {...register('emergency_contact.relationship')} style={inputStyle} />
        </div>
      </section>

      {/* Clinical Information Section */}
      <section style={formSectionStyle}>
        <h2>Clinical Information</h2>
        <div style={fieldStyle}>
          <label htmlFor="primary_care_physician" style={labelStyle}>Primary Care Physician</label>
          <input id="primary_care_physician" {...register('primary_care_physician')} style={inputStyle} />
        </div>
        {/* Add other clinical information fields as needed */}
      </section>

      <button type="submit" disabled={isLoading} style={buttonStyle}>
        {isLoading ? 'Submitting...' : (defaultValues?.id ? 'Update Patient' : 'Register Patient')}
      </button>
    </form>
  );
};

export default PatientRegistrationForm;
